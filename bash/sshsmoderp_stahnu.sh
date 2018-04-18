if [ $# -eq 0 ]
  then
    echo "chyby argumenty
    ./bash/sshsmoderp_stahnu.sh [output adresar] [log soubor]"
    echo
    exit
fi

if [ $# -eq 1 ]
  then
    echo "chyby jeste jeden argument  
    ./bash/sshsmoderp_stahnu.sh [output adresar] [log soubor]"
    echo
    exit
fi

echo je adresar a log spravne?
read

rsync -ave ssh sshsmoderp:/home/smoderp/$1/* $1 
rsync -ave ssh sshsmoderp:/home/smoderp/$2 $2