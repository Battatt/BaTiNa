from random import choice, shuffle, randint
import string


def steam_keys_generator():
    chars = "QWERTYUIOPASDFGHJKLZXCVBNM0123456789"

    first_key = ''.join(choice(chars) for _ in range(5))
    second_key = ''.join(choice(chars) for _ in range(5))
    third_key = ''.join(choice(chars) for _ in range(5))
    key = first_key + '-' + second_key + '-' + third_key

    while any(first_key[i] == second_key[i] or first_key[i] == third_key[i] or second_key[i] == third_key[i] for i in
              range(5)):
        first_key = ''.join(choice(chars) for _ in range(5))
        second_key = ''.join(choice(chars) for _ in range(5))
        third_key = ''.join(choice(chars) for _ in range(5))

        key = first_key + '-' + second_key + '-' + third_key
    return key


def telegram_key_generator():
    chars = "qwertyuiopasdfghjkl----zxcvbnm~!@#%$*(@#)*-+=_?&$QWERTYUIOPASDFGHJKLZXCVBNM0123456789"
    key = ''.join(choice(chars) for _ in range(20))

    while len(set(key)) < 10:
        key = ''.join(choice(chars) for _ in range(20))

    return key


def robux_redeem_code_generator():
    chars = "RBLXUUUINBV0123456789KZXCOOO"
    key = ''.join(choice(chars) for _ in range(16))

    while len(set(key)) < 12:
        key = ''.join(choice(chars) for _ in range(16))

    return key


def discord_nitro_key_generator():
    chars = "QWERTYUIOPASDFGHJKLZXCVBNM0123456789"
    key_1 = ''.join(choice(chars) for _ in range(4))
    key_2 = ''.join(choice(chars) for _ in range(5))
    key_3 = ''.join(choice(chars) for _ in range(5))
    key_4 = ''.join(choice(chars) for _ in range(5))
    key = key_1 + '-' + key_2 + '-' + key_3 + '-' + key_4

    while any(
            key_1[i] == key_2[i] or key_1[i] == key_3[i] or key_1[i] == key_4[i] or key_2[i] == key_3[i] or key_2[i] ==
            key_4[i] or key_3[i] == key_4[i] for i in range(4)):
        key_1 = ''.join(choice(chars) for _ in range(4))
        key_2 = ''.join(choice(chars) for _ in range(5))
        key_3 = ''.join(choice(chars) for _ in range(5))
        key_4 = ''.join(choice(chars) for _ in range(5))

        key = key_1 + '-' + key_2 + '-' + key_3 + '-' + key_4
    return key


def any_code_generator():
    chars = string.ascii_uppercase + string.ascii_lowercase + string.digits + '=+-!@#$%^&*№?'
    code_length = randint(10, 20)
    code = choice(string.ascii_uppercase)

    while len(code) < code_length:
        next_char = choice(chars)
        if next_char != code[-1]:
            code += next_char

    code_list = list(code)
    shuffle(code_list)
    code_shuffled = ''.join(code_list)

    return code_shuffled


if __name__ == "__main__":
    print(steam_keys_generator())
    print(telegram_key_generator())
    print(robux_redeem_code_generator())
    print(discord_nitro_key_generator())
