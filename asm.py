#!/usr/bin/python3


from flask import *
from pyratemp import *
import time
import re
from subprocess import *
from pathlib import Path
import shutil

app = Flask(__name__)

WELCOME_CODE = '''MOV r0, #20
MOV r1, #-4
ADD r2, r0, r1
// Máte k dispozici 4MB paměti od adresy 0x100000
MOV r5, #0x100000
STR r2, [r5]
'''
REGS = [ 'r%d'%i for i in range(13) ]

MY_DIR = Path(os.path.abspath(os.path.dirname(__file__)))
os.chdir(MY_DIR)
TMP_DIR = MY_DIR / 'tmp'
SESS_LIFETIME = 300

def cleanup_sessions():
    for chld in TMP_DIR.iterdir():
        if time.time() - chld.stat().st_mtime > SESS_LIFETIME:
            shutil.rmtree(str(chld))
            call(['isolate', '--cg', '--cleanup', '-b', chld.name])
            

def allocate_sid():
    cleanup_sessions()
    for sid in range(999):
        sess_dir = TMP_DIR / str(sid)
        try: sess_dir.mkdir()
        except FileExistsError: continue
        return sid, sess_dir

def err_postproc(out):
    lines = out.splitlines()
    r = []
    m = None
    def match(regex):
        nonlocal m
        m = re.match("^"+regex+"$", line)
        return m
    for line in lines:
        if match(r"\S+: In function `([^']+)':"):
            if m.group(1) == 'main': continue
            line = "V kódu pod návěštím %s:" % m.group(1)
        elif match(r"\S+: Assembler messages:"):
            continue
        elif match(r"\S+: undefined reference to `([^']+)'"):
            line = "Skok na neexistující návěští '%s'" % m.group(1)
        elif match(r"collect2: error: ld returned \d+ exit status"):
            continue
        elif match(r"\S+: Error: invalid constant \(([^)]+)\) after fixup"):
            line = "Neplatná číselná konstanta %s, např. příliš velká" % m.group(1)
        elif match(r"\S+: Error: bad instruction `([^']+)'"):
            line = "Neplatná instrukce: '%s'" % m.group(1)
        elif match(r"Time limit exceeded"):
            line = "Vypršel časový limit (pravděpodobně nekonečná smyčka)"
        elif match(r"qemu: uncaught target signal 11.*"):
            continue
        elif match(r"/bin/bash:.*"):
            continue
        elif match(r"Exited with error status 139"):
            line = "Přístup na neplatnou paměťovou adresu"
        elif match(r"Exited with error status \d+"):
            continue
        r.append(line)
    return '\n'.join(r)


GCC = '/usr/bin/arm-linux-gnueabihf-gcc'
QEMU_FN =  '/usr/bin/qemu-arm'
index_tpl = Template(open('templates/index.html','r').read())
source_tpl = Template(open('source.c.tpl','r').read(), escape=None)

THREAD_RE = re.compile(r'^\s*thread([0-9]+)\s*:', re.M)

@app.route('/', methods=['GET', 'POST'])
def index():
    regs = None
    out = None
    state = 'unknown'
    gcc_add = []
    if request.method == 'POST':
        code = request.form['code']
        threads = [ int(x) for x in THREAD_RE.findall(code) ]
        print(threads)
        if threads:
            gcc_add.append('-pthread')
        sid, sess_dir = allocate_sid()
        box = str(sid)
        try:
            call(['isolate', '--cg', '--cleanup', '-b', box])
            check_call(['isolate', '--cg', '--init', '-b',box])
            src_fn = sess_dir / 'source.c'
            bin_fn = sess_dir / 'a.out'
            sess_dir.chmod(0o777)
            c_source = source_tpl(source=code, threads=threads)
            with src_fn.open('w') as fd:
                fd.write(c_source)
            try: bin_fn.unlink()
            except FileNotFoundError: pass
            proc = Popen(['isolate', '--cg', '-b', box, '-p10',  '--run',
                            '-d', str(sess_dir)+':rw',
                            '--cg-timing', '--cg-mem=32768', '--time=5', '--wall-time=15',
                            '--',
                            GCC, '-static', '-mcpu=cortex-a7', '-mtune=cortex-a7',
                                            '-mfpu=neon', '-marm',
                            '-o', str(bin_fn), '-std=gnu11', str(src_fn)] + gcc_add,
                            stdout=PIPE, stderr=STDOUT)
            out, _ = proc.communicate()
            if proc.wait() == 0:
                proc = Popen(['isolate', '--cg', '-b', box, '-p10',  '--run',
                                '-d', str(sess_dir)+':rw',
                                '--cg-timing', '--cg-mem=32768', '--time=5', '--wall-time=15',
                                '--',
                                # Without restricting the core ulimit, it hangs on segfault
                                "/bin/bash", "-c", "ulimit -c 0; exec " + str(QEMU_FN) + " " + str(bin_fn),
                                ],
                                stdout=PIPE, stderr=STDOUT)
                out, _ = proc.communicate()
                out = err_postproc(out.decode('utf-8', 'ignore'))
                if proc.wait() == 0:
                    state = 'ok'
                else:
                    state = 'run-fail'
            else:
                out = err_postproc(out.decode('utf-8', 'ignore'))
                state = 'compile-fail'
        finally:
            call(['isolate', '--cg', '--cleanup', '-b', box])
            #shutil.rmtree(str(sess_dir))
    else:
        code = WELCOME_CODE
    return index_tpl(code=code, regs=regs, out=out, state=state)

if __name__ == '__main__': app.run()
