
zip smoderp-stable.zip main.py main_src/flow_algorithm/*.py main_src/stream_functions/*.py main_src/io_functions/*.py  main_src/tools/*.py main_src/processes/*.py main_src/main_classes/*.py main_src/*.py

tar -czf smoderp-stable.tar.gz main.py main_src/flow_algorithm/*.py main_src/stream_functions/*.py main_src/io_functions/*.py  main_src/tools/*.py main_src/processes/*.py main_src/main_classes/*.py main_src/*.py

rsync  -Rave ssh  smoderp-stable.zip sshsmoderp:/home/smoderp/public_html/

rsync  -Rave ssh  smoderp-stable.tar.gz sshsmoderp:/home/smoderp/public_html/

rsync -Rave ssh main.py main_src/flow_algorithm/*.py main_src/stream_functions/*.py main_src/io_functions/*.py  main_src/tools/*.py main_src/processes/*.py main_src/main_classes/*.py main_src/*.py sshsmoderp:/home/smoderp/public_html/stable/

rm smoderp-stable.zip smoderp-stable.tar.gz
