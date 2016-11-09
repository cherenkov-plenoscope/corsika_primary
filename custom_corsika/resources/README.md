#How to diff and path

Make a diff from the original using
```bash
diff -Naur corsika-75600/bernlohr/iact.c my_custom_iact.c > iact.c.diff
```

and apply the diff to the original using
```bash
patch corsika-75600/bernlohr/iact.c iact.c.diff
```