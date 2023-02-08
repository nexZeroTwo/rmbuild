# rmbuild
RocketMinsta build system

So, you want to locally install RM on your Nexuiz installation. This guide is for Linux, as I have no idea how MacOS works and Windows is a pain.
If you insist on using Windows, download WSL (Windows Subsystem for Linux) - a good tool to compile and do things flawlessly on Windows via Linux.
For this, you must use Terminal; as the GUI that Linux provides is very limited (I write this mainly for newbies to Linux, such as me.)

# Step 1: 
Download Nexuiz 2.5.2, e.g. https://sourceforge.net/projects/nexuiz/files/NexuizRelease/Nexuiz%202.5.2/

Create in your /home directory: ```.nexuiz/data```

# Step 2: 
Clone the repositories to your /home destinations; or wherever you want.
```
git clone https://github.com/nexZeroTwo/RocketMinsta
git clone https://github.com/nexZeroTwo/DarkPlacesRM
git clone https://github.com/nexZeroTwo/rmqcc
git clone https://github.com/nexZeroTwo/rmbuild
```

RocketMinsta contains all relevant files for the server itself, RMQCC is the compiler, DarkPlacesRM is the engine that will compile your dedicated Nexuiz file.

# Step 3: 
Starting with RMQCC.
Go inside your rmqcc folder, inside it.

Install build-essentials, with: ```sudo apt-get install build-essential cmake```

Inside your rmqcc folder, write: ```sudo make```

After that, you will get a file called rmqcc.bin. This has to be copied to usr/bin/rmqcc. To fasten the process, here's your command: ```sudo cp rmqcc.bin /usr/bin/rmqcc```

If you've got past this stage, you're done compiling your RMQCC compiler!

# Step 4: 
Continuing with RMBuild, this is important - as this basically tells your RocketMinsta installation how to proceed.

If you do not have python3 installed, which causes an error, do this: ```sudo apt-get install python3-pip```

If you do not have setuptools installed, which causes an error, do this: ```pip install setuptools``` (do NOT run under sudo, as it will tell you to run it as non-root)

After that, do: ```sudo ./setup.py install```

It should output something like: ```Finished processing dependencies for rmbuild==0.1```
This means, you're done!

# Step 4: 
RocketMinsta install
Go to your RM install folder, that you cloned.

Copy the script provided in "rmbuild" named "example_config.py" to "RocketMinsta"

Rename it to "config.py". (THIS is IMPORTANT!) - here's your command: ```mv ~/rmbuild/example_config.py ~/RocketMinsta/config.py```

If you've done this, do this inside RocketMinsta: ```sudo python3 build.py```

Good, it's going to drop everything inside: ```~/.nexuiz/data/```

Note: If it says "file not found", try editing (via Windows or VIM) the Line 64 on config.py.

Example: install_dirs = [util.expand('/home/zero/.nexuiz/data')]

Make sure to also copy the "zzz" files to your ~/Nexuiz/data/ (basically where your Nexuiz 2.5.2 installation is).

# IMPORTANT
Do copy ```Nexuiz/data/data20091001.pk3``` to: ```./nexuiz/data```

Do copy ```.nexuiz/data``` to ```usr/share/games``` (will look like this: ```usr/share/games/nexuiz/data```

Just make sure all 3 locations (usr, Nexuiz, .nexuiz) have all zzz-rm packages included, as well as the data20091001.pk3!

Depending on your distro, you will need root privilege!

# Step 5: 
Your Nexuiz-DPRM install:

Go to your cloned folder called DarkPlacesRM.

You might be missing multiple packages, so install them via: ```sudo apt-get install libjpeg-dev libpng-dev``` and ```sudo apt install pkg-config```

Inside DarkPlacesRM, write: ```make sv-nexuiz```. This will compile your own nexuiz-dprm-dedicated version. 

Copy this inside your Nexuiz installation. (e.g. ./Nexuiz)

-> Do ```chmod +x ./nexuiz-dprm-dedicated``` | This allows your dedicated Nexuiz file to be executed.

# Step 6:
Executing and customizing

First, do ```ip address``` in terminal to find out your own address. With this, you can connect via your Rexuiz/Xonotic client to your local Nexuiz-DPRM server.

Open your dedicated Nexuiz file, do: ```./nexuiz-dprm-dedicated```

Do ```exec rocketminsta.cfg```, this will execute RocketMinsta files. Do ```restart``` to apply the changes, and you're good to go!

You don't have to really customize them, as the hooks provide you with enough cfgs.
