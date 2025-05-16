# UnitTestShow
``
convert unit test result(xml) to html
``

## 1.Init submodule
```commandline
git submodule update --init --recursive
or
git submodule init
git submodule update
```
## 2.Put test result into xml/ or specify test result dir
## 3.Usage
```commandline
# if put test result into xml/
python3 convert.py
# or check the script's usage 
python3 convert.py -h
```
## 4.Others
- [git submodule usage](https://www.cnblogs.com/jyroy/p/14367776.html)
- [gtest run args](https://www.jianshu.com/p/f867e87f3b7d)
- [gtest guide](https://google.github.io/googletest/)