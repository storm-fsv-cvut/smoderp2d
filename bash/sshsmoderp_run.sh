if [ $# -eq 0 ]
  then
    echo "chyby log soubot 
    ./bash/sshsmoderp_run.sh [log]"
    echo
    exit
fi

./bash/sshsmoderp_up.sh
cat ./a.sh
echo
echo smoderp bezi...
ssh sshsmoderp "./a.sh > $1" 
