"""받은 인자를 한 줄에 하나씩 repr 로 찍는다. `run.sh` 가 네이티브 프로그램 자리에 둔다."""

import sys

for argument in sys.argv[1:]:
    print(repr(argument))
