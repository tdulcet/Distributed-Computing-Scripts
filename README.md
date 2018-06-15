# Distributed Computing Scripts
Linux Distributed Computing Scripts

Copyright © 2018 Teal Dulcet

## 	Great Internet Mersenne Prime Search (GIMPS)

### Prime95/MPrime

Downloads, sets up and runs Prime95.

```
wget https://raw.github.com/tdulcet/Distributed-Computing-Scripts/master/mprime.sh -qO - | bash -s -- [PrimeNet User ID] [Computer name] [Type of work] [Idle time to run]
```

To run Prime95 for Stress/Torture Testing, see here: https://github.com/tdulcet/Testing-and-Benchmarking-Scripts.

### CUDALucas

Downloads, sets up and runs CUDALucas.

```
wget https://raw.github.com/tdulcet/Distributed-Computing-Scripts/master/cudalucas.sh -qO - | bash -s -- <PrimeNet Password> [PrimeNet User ID] [Type of work] [Idle time to run]
```

## 	BOINC

Downloads, installs and sets up BOINC.

```
wget https://raw.github.com/tdulcet/Distributed-Computing-Scripts/master/boinc.sh -qO - | bash -s -- <Project URL> <E-mail> <Password>
```

OR

```
wget https://raw.github.com/tdulcet/Distributed-Computing-Scripts/master/boinc.sh -qO - | bash -s -- <Project URL> <Account Key>
```

## 	Folding@home

Downloads, installs and sets up Folding@home.

```
wget https://raw.github.com/tdulcet/Distributed-Computing-Scripts/master/folding.sh -qO - | bash -s -- [Username] [Team number] [Passkey] [Power]
```

These scripts should work on Ubuntu and any Linux distribution that can use the apt package manager.
