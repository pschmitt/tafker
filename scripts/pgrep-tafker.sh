#!/usr/bin/env bash

watch -n .25 -d "pgrep -iaf tafker | grep -vE 'watch|vim|ipython|$0'"
