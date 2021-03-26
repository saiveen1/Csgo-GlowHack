import pymem.process
import win32con as keymap
import re
from pymem import Pymem
from win32api import GetAsyncKeyState

exitKey = keymap.VK_END
show_teammate_button = keymap.VK_F1
glow_toggle = keymap.VK_F2


class ColorRGBA:
    Red = 0
    Green = 0
    Blue = 0
    Alpha = 0

    def __init__(self, r, g, b, a):
        self.Red = r
        self.Green = g
        self.Blue = b
        self.Alpha = a


def key_pressed(key):
    return GetAsyncKeyState(key) & 1 == 1


def glow(h_game: pymem, glow_manager, entity_glow, color: ColorRGBA):
    h_game.write_float(glow_manager + entity_glow * 0x38 + 0x4, float(color.Red))
    h_game.write_float(glow_manager + entity_glow * 0x38 + 0x8, float(color.Green))
    h_game.write_float(glow_manager + entity_glow * 0x38 + 0xC, float(color.Blue))
    h_game.write_float(glow_manager + entity_glow * 0x38 + 0x10, float(color.Alpha))
    h_game.write_uchar(glow_manager + entity_glow * 0x38 + 0x24, 1)
    h_game.write_uchar(glow_manager + entity_glow * 0x38 + 0x25, 0)


def main():

    b_glow_teammate = False
    b_glow = True
    enemy_color = ColorRGBA(0, 1, 0, 1)
    teammate_color = ColorRGBA(0, 0, 1, 1)
    handle: Pymem = pymem.Pymem("csgo.exe")
    client = pymem.process.module_from_name(handle.process_handle, "client.dll")
    client_module = handle.read_bytes(client.lpBaseOfDll, client.SizeOfImage)
    local_addr = client.lpBaseOfDll + re.search(rb'\x8b\x35.{4}\x57\x85\xf6\x74\x56', client_module).start() + 2
    glow_manger_addr = client.lpBaseOfDll + re.search(rb'\x0f\x11\x05.{4}\x83\xc8\x01', client_module).start() + 3
    entity_list_addr = client.lpBaseOfDll + re.search(rb'\x56\x8b\x89.{4}\x85\xc9\x74\x1b', client_module).start() + 3
    glow_index_addr = client.lpBaseOfDll + re.search(rb'\x8B\x7d\xec\x8b\xb3.{4}', client_module).start() + 5
    health_addr = client.lpBaseOfDll + re.search(rb'\x83\xb9.{4}\x00\x7f\x2d\x8b\x01', client_module).start() + 2
    team_addr = client.lpBaseOfDll + re.search(rb'\xcc\x8b\x89.{4}\xe9.{4}\xcc', client_module).start() + 3

    glow_manager_ptr = handle.read_uint(glow_manger_addr)
    entity_list_ptr = handle.read_uint(entity_list_addr)
    m_glow_index = handle.read_uint(glow_index_addr)
    m_health = handle.read_uint(health_addr)
    m_team = handle.read_uint(team_addr)

    print("Glow has launched.")
    print("Press F1 to show teammates.")
    print("Press F2 to turn the glow on/off.")
    print("Press END to quit.")
    
    try:
        while True:
            glow_manager = handle.read_uint(glow_manager_ptr)
            if key_pressed(exitKey):
                break
            if key_pressed(show_teammate_button):
                b_glow_teammate = not b_glow_teammate
                print("Team glow is " + ("on" if b_glow_teammate is True else "close"))
            if key_pressed(glow_toggle):
                b_glow = not b_glow
                print("Glow is " + ("on" if b_glow is True else "close"))

            local_player_ent = handle.read_uint(handle.read_uint(local_addr))
            if local_player_ent:
                local_team = handle.read_uint(local_player_ent + m_team)
                if b_glow:
                    for i in range(1, 32):
                        entity = handle.read_uint(entity_list_ptr + i * 0x10)

                        if entity:
                            entity_team = handle.read_uint(entity + m_team)
                            if not b_glow_teammate:
                                if entity_team == local_team:
                                    continue
                            entity_glow = handle.read_uint(entity + m_glow_index)

                            if entity_team == local_team:
                                glow(handle, glow_manager, entity_glow, teammate_color)
                            else:
                                ent_health = handle.read_uint(entity + m_health)
                                enemy_color.Green = 0.006 * ent_health
                                if ent_health == 0x64:
                                    enemy_color.Green = 1
                                enemy_color.Red = 1.0 - enemy_color.Green
                                glow(handle, glow_manager, entity_glow, enemy_color)

    finally:
        handle.close_process()


if __name__ == '__main__':
    main()
