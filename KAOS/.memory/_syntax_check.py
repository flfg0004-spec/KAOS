import sys
sys.path.insert(0, '.memory/_scripts/lib')
compile(open('.memory/_scripts/lib/obsidian.py', encoding='utf-8').read(), 'obsidian.py', 'exec')
print('✅ obsidian.py syntax OK')
