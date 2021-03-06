import os, shutil, sys, tarfile, time


CC = "clang -target i386-pc-none-elf -w -mno-sse -mno-avx -std=gnu99 -ffreestanding -I kernel/include/ -c"


def build_kernel():
    start_time = time.time()

    print("Building kernel")

    SRC_TARGETS = []
    BIN_TARGETS = []
    
    for path, directories, files in os.walk("kernel\\"):
        for i in files:
            if i.endswith('.c'):
                SRC_TARGETS.append(os.path.join(path, i))
                BIN_TARGETS.append(os.path.join("bin\kernel\\", os.path.splitext(i)[0]+'.o'  ))
            elif i.endswith('.s'):
                SRC_TARGETS.append(os.path.join(path, i))
                BIN_TARGETS.append(os.path.join("bin\kernel\\", os.path.splitext(i)[0]+'_ASM.o'  ))

    shutil.rmtree("bin/kernel/", ignore_errors=True)
    os.mkdir("bin/kernel/")
    
    for i in range(0, len(SRC_TARGETS)):
        os.system(f"{CC} {SRC_TARGETS[i]} -o {BIN_TARGETS[i]}")
        

    # Получаем список файлов в переменную files
    files = os.listdir("bin/kernel/")

    # Фильтруем список
    bins = filter(lambda x: x.endswith('.o'), files)
    OBJ = ""
    
    for i in bins:
        OBJ += f"bin/kernel/{i} "
    print(f"OBJ={OBJ}")

    os.system("ld.lld -T kernel/link.ld -nostdlib -o isodir/boot/kernel.elf " + OBJ)
    print(f"Build end at: {time.time() - start_time}")



def build_apps():
    os.chdir("apps/")
    os.system("python build.py")

    shutil.rmtree("../initrd/apps", ignore_errors=True)
    shutil.copytree("../bin/apps", "../initrd/apps")

    os.chdir("../initrd")
        

    with tarfile.open("../isodir/boot/initrd.tar", "w") as tar:
        for i in os.listdir():
            tar.add(i)
    os.chdir("../")


def create_iso():
    print("Creating ISO with grub")
    start_time = time.time()

    if sys.platform == "linux" or sys.platform == "linux2":
        os.system("grub-mkrescue -o \"SynapseOS.iso\" isodir/ -V SynapseOS")
    else:
        os.system("ubuntu run grub-mkrescue -o \"SynapseOS.iso\" isodir/ -V SynapseOS ")
    
    print(f"Build end at: {time.time() - start_time}")


def create_iso_l():
    print("Creating ISO with limine")
    start_time = time.time()

    os.system("git clone https://github.com/limine-bootloader/limine.git --branch=v3.0-branch-binary --depth=1")
    os.system("make -C limine")
    os.system("mkdir -p iso_root")
    os.system("""cp -v isodir/boot/kernel.elf limine.cfg limine/limine.sys \
        limine/limine-cd.bin limine/limine-cd-efi.bin iso_root/
    """)
    os.system("""xorriso -as mkisofs -b limine-cd.bin \
          -no-emul-boot -boot-load-size 4 -boot-info-table \
          --efi-boot limine-cd-efi.bin \
          -efi-boot-part --efi-boot-image --protective-msdos-label \
          iso_root -o SynapseOS.iso""")
    os.system("./limine/limine-deploy SynapseOS.iso")
    
    print(f"Build end at: {time.time() - start_time}")


def run_qemu():
    if os.path.exists("ata.vhd"):
        pass
    else:
        os.system("qemu-img create -f raw ata.vhd 32M")
    
    qemu_command = "qemu-system-i386 -name SynapseOS -soundhw all -m 16" \
        " -netdev socket,id=n0,listen=:2030 -device rtl8139,netdev=n0,mac=11:11:11:11:11:11 " \
        " -cdrom SynapseOS.iso -hda ata.vhd -serial  file:Qemu.log"
        
    os.system(
        qemu_command
        )


if __name__ == "__main__":
    try:
        start_time = time.time()

        # Стандартная сборка
        
        if len(sys.argv) == 1:
            build_kernel()
            build_apps()
            create_iso()
            run_qemu()
        else:
            for i in range(1, len(sys.argv)):
                if sys.argv[i] == "kernel":
                    build_kernel()
                elif sys.argv[i] == "apps":
                    build_apps()
                elif sys.argv[i] == "iso":
                    create_iso()
                elif sys.argv[i] == "run":
                    run_qemu()
                elif sys.argv[i] == "autobuild":
                    print("***************AUTOBUILD***************************")
                    build_kernel()
                    #build_apps()
                    #create_iso_l()
                else:
                    print(f"Ошибка, неизвестный аргумент: {sys.argv[i]}")
        print(f"Конец: {time.time() - start_time}")

    except Exception as E:
        print(E)