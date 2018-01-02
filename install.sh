if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root. " >&2
    exit
fi

if ! [ -x "$(command -v pip3)" ]; then
    echo 'Error: Python3 or pip3 is not installed.' >&2
    exit 1
fi
if ! [-x "$(command -v tesseract)" ]; then
    echo 'Error: Tesseract is not installed.' >&2
    exit 1
fi
if ! [[ $(tesseract -v | grep 'tesseract 3\.05\..*\|tesseract 4.*') ]]; then
    echo 'Error: Tesseract version requirement not met. Tesseract version 3.05 or higher required.' >&2
    exit 1
fi

TESSDATA_DIR=''

if ! [[ $(ls /usr/local/share/tessdata/) | grep 'No such file or directory']]; then
    TESSDATA_DIR='/usr/local/share/tessdata/' 
elif ! [[ $(/usr/share/tesseract-ocr/tessdata/) | grep 'No such file or directory']]; then
    TESSDATA_DIR='/usr/share/tesseract-ocr/tessdata/' 
else
    echo 'Error: Tesseract directory not found.' >&2
    exit 1
fi

pip3 install -r dependencies.txt
cp pubg.traineddata TESSDATA_DIR
cp pubg_start.traineddata TESSDATA_DIR

echo 'Installed.'
exit 0
