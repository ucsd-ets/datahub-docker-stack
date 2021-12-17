#!/bin/bash

# Adapted from https://stackoverflow.com/a/52543399/6029703

if [ "$#" -gt 2  -o  "$#" -lt 1 ]; then
    echo "********************************************************************"
    echo "*                        Knitter version 1.1                       *"
    echo "********************************************************************"
    echo -e "This script converts Rmd files into HTML (default) or PDFs. \n"
    echo -e "usage: knitter file.Rmd [output_format] \n"
    exit
fi

# Get extension of file
ext=`echo $1 | cut -f2 -d.`


case $2 in
  '')
    format=''
    ;;

  pdf_document | pdf | PDF)
    format="pdf_document"
    ;;

  html_document | html | HTML | htm | HTM)
    format="html_document"
    ;;

  ioslides_presentation | ioslides | slides | presentation)
    format="ioslides_presentation"
    ;;

  slidy_presentation | slidy | Slidy)
    format="slidy_presentation"
    ;;

  beamer_presentation | beamer | Beamer)
    format="beamer_presentation"
    ;;

  powerpoint_presentation | powerpoint | PowerPoint | ppt | PPT | pptx | PPTX)
    format="powerpoint_presentation"
    ;;

  word_document | word | Word | doc | DOC | docx | DOCX)
    format="word_document"
    ;;

  word_document | word | Word | doc | DOC | docx | DOCX)
    format="word_document"
    ;;

  md_document | md | MD | Markdown | markdown)
    format="md_document"
    ;;

  *)
    echo "unknown"
    exit 1
    ;;
esac


### Test if file exist
if [[ ! -r $1 ]]; then
    echo -e "\n File does not exist, or option mispecified \n"
    exit
fi

### Test file extension
if [[ "$ext" =~ \.[Rr][Mm][Dd]$ ]]; then
    echo -e "\n Invalid input file, must be a Rmd-file \n"
    exit
fi

# Create temporary script
# Use user-defined 'TMPDIR' if possible; else, use /tmp
if [[ -n $TMPDIR ]]; then
    pathy=$TMPDIR
else
    pathy=/tmp
fi

# Tempfile for the script
tempscript=`mktemp $pathy/tempscript.XXXXXX` || exit 1

if [[ $format ]] ; then
    echo "library(rmarkdown); rmarkdown::render('"${1}"', '"$format"')" >> $tempscript
else
    echo "library(rmarkdown); rmarkdown::render('"${1}"')" >> $tempscript
fi

cat $tempscript
Rscript $tempscript