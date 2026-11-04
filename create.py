import os



BOOT1_FILE = "boot1.bin"




# Lista de archivos a meter dentro de la imagen

FILES_TO_ADD = ["KERNEL.BIN", "hola.bin","calc.bin","map.bin","bios.bin",]



OUTPUT_IMG = "esp16.img"



BYTES_PER_SECTOR = 512

TOTAL_SECTORS = 2880

RESERVED_SECTORS = 17

SECTORS_PER_FAT = 9

ROOT_START_SECTOR = 35

DATA_START_SECTOR = 49



def format_83(filename):

    """Convierte un nombre de archivo al formato FAT 8.3 en mayúsculas."""

    name, ext = os.path.splitext(filename)

    ext = ext.lstrip('.')

    return f"{name[:8].upper():<8}{ext[:3].upper():<3}".encode('ascii')



def set_fat12_entry(fat, cluster, val):

    """Escribe un valor de 12 bits en la tabla FAT12."""

    offset = (cluster * 3) // 2

    if cluster % 2 == 0:

        fat[offset] = val & 0xFF

        fat[offset + 1] = (fat[offset + 1] & 0xF0) | ((val >> 8) & 0x0F)

    else:

        fat[offset] = (fat[offset] & 0x0F) | ((val & 0x0F) << 4)

        fat[offset + 1] = (val >> 4) & 0xFF



def build_image():

    image = bytearray(TOTAL_SECTORS * BYTES_PER_SECTOR)



    # 1. Copiar Boot1 (Sector 0)

    with open(BOOT1_FILE, "rb") as f:

        boot1 = f.read()

    image[0:len(boot1)] = boot1


    # 3. Inicializar Tabla FAT12

    fat = bytearray(SECTORS_PER_FAT * BYTES_PER_SECTOR)

    fat[0] = 0xF0

    fat[1] = 0xFF

    fat[2] = 0xFF



    current_cluster = 2

    root_offset = ROOT_START_SECTOR * BYTES_PER_SECTOR

    entry_index = 0



    for fname in FILES_TO_ADD:

        if not os.path.exists(fname):

            print(f"Error: El archivo {fname} no existe en el directorio.")

            return



        with open(fname, "rb") as f:

            data = f.read()



        size = len(data)

        num_clusters = (size + BYTES_PER_SECTOR - 1) // BYTES_PER_SECTOR

        start_cluster = current_cluster



        # Escribir la cadena de clústeres en la FAT12

        for i in range(num_clusters):

            c = start_cluster + i

            nxt = 0xFFF if i == num_clusters - 1 else c + 1

            set_fat12_entry(fat, c, nxt)



        # Entrada de 32 bytes en el Directorio Raíz

        entry = bytearray(32)

        entry[0:11] = format_83(os.path.basename(fname))

        entry[11] = 0x20  # Atributo: Archivo normal

        entry[26] = start_cluster & 0xFF

        entry[27] = (start_cluster >> 8) & 0xFF

        entry[28] = size & 0xFF

        entry[29] = (size >> 8) & 0xFF

        entry[30] = (size >> 16) & 0xFF

        entry[31] = (size >> 24) & 0xFF



        image[root_offset + entry_index * 32 : root_offset + (entry_index + 1) * 32] = entry

        entry_index += 1



        # Escribir contenido en el área de datos (DATA_START)

        sector_lba = DATA_START_SECTOR + (start_cluster - 2)

        data_offset = sector_lba * BYTES_PER_SECTOR

        image[data_offset : data_offset + size] = data



        current_cluster += num_clusters



    # Guardar las dos copias de la FAT en la imagen

    fat1_off = RESERVED_SECTORS * BYTES_PER_SECTOR

    fat2_off = (RESERVED_SECTORS + SECTORS_PER_FAT) * BYTES_PER_SECTOR

    image[fat1_off : fat1_off + len(fat)] = fat

    image[fat2_off : fat2_off + len(fat)] = fat



    with open(OUTPUT_IMG, "wb") as f:

        f.write(image)



    print(f"OK: {OUTPUT_IMG} generado con los archivos: {', '.join(FILES_TO_ADD)}")



if __name__ == "__main__":

    build_image() 