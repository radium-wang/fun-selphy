"""Reproduce CP1500 static clock configuration and scatter-table evidence.

Clock arithmetic follows boot.bin file offsets 0xa0c4, 0xa150, 0xa3c8.
This is configuration evidence, not an on-device clock/RAM measurement.
"""
from pathlib import Path
import json
import struct

ROOT = Path(__file__).resolve().parent


def audit(version):
    folder = ROOT / 'unpacked' / version
    prefix = (folder / 'prefix-640KiB.decoded.bin').read_bytes()
    main = (folder / 'main.bin').read_bytes()
    count = struct.unpack_from('<I', prefix)[0]
    registers = {}
    for i in range(count):
        address, value = struct.unpack_from('<IB', prefix, 8 + i * 5)
        registers[address] = value

    def word(address):
        return sum(registers[address + i] << (8 * i) for i in range(4))

    clocks = {}
    for name, address in [('main', 0xf0000028), ('cpu', 0xf000002c)]:
        config = word(address)
        source = (config >> 24) & 15
        divisor = config & 0xfffff
        assert not config & 0x100000, 'fractional mode needs different formula'
        pll_address = {2: 0xf00000c0, 3: 0xf00000c4,
                       4: 0xf00000c8, 5: 0xf00000cc}[source]
        pll = word(pll_address)
        assert pll & 0x1000000
        frequency = ((pll & 31) + 64) * 12_000_000 // (divisor or 1)
        clocks[name] = {'config_address': hex(address), 'config': hex(config),
                        'pll_address': hex(pll_address), 'pll': hex(pll),
                        'initial_hz': frequency}
    scatter = []
    for offset in range(0x198, 0x228, 16):
        source, dest, size, handler = struct.unpack_from('<4I', main, offset)
        scatter.append({'table_file_offset': hex(offset), 'source': hex(source),
                        'destination': hex(dest), 'size': hex(size),
                        'handler': hex(handler),
                        'source_file_offset_if_copied': hex(source - 0x071b8000)})
    return {'version': version, 'initial_register_records': count,
            'clocks': clocks, 'main_scatter_table': scatter,
            'ram_pool': {'base': '0x41f00000', 'size': '0x060e0000',
                         'end_exclusive': '0x47fe0000', 'size_mib': 0x60e0000/2**20,
                         'evidence': 'main.bin file offsets 0x1334..0x1344',
                         'physical_capacity_inference_mib': 128,
                         'physical_capacity_confirmed_on_hardware': False}}


if __name__ == '__main__':
    result = [audit(v) for v in ['1060', '1070']]
    output = ROOT / 'analysis' / 'hardware-audit.json'
    output.write_text(json.dumps(result, indent=2) + '\n')
    print(output)
    for item in result:
        print(item['version'], item['clocks'], item['ram_pool'])
