@echo off
py -3 -c "compile(open('C:\\Users\\LeonX\\Documents\\KAOS\\.memory\\_scripts\\lib\\agent_nodes\\kosmos.py', encoding='utf-8').read(), 'path', 'exec')" && echo SYNTAX OK || echo SYNTAX ERROR