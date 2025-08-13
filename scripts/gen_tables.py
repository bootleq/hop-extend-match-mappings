import os
import glob
import re
import pprint

def main():
    # Ensure tmp directory exists
    os.makedirs('tmp', exist_ok=True)

    # Step 1: Parse CNS_source.txt and create tmp/pass1.csv
    # Filters CNS_source.txt for entries containing "常用" in the second column.
    # Saves the CNS code (first column) to tmp/pass1.csv.
    cns_source_path = 'data/CNS_source.txt'
    pass1_path = 'tmp/pass1.csv'
    cns_codes_to_process = set() # Stores CNS codes from pass1 for subsequent steps
    found_sources = set()

    try:
        with open(cns_source_path, 'r', encoding='utf-8') as infile, \
             open(pass1_path, 'w', encoding='utf-8') as outfile:
            for line in infile:
                parts = line.strip().split('\t')
                if len(parts) >= 2 and '常用' in parts[1]:
                    cns_code = parts[0]
                    outfile.write(f"{cns_code}\n")
                    cns_codes_to_process.add(cns_code)
                    found_sources.add(parts[1])
        print(f"Step 1 completed: {len(cns_codes_to_process)} CNS codes with '常用' saved to {pass1_path}")
        print("Used sources:\n" + pprint.pformat(found_sources, 2))
    except FileNotFoundError:
        print(f"Error: {cns_source_path} not found.")
        return

    # Step 2: Generate tmp/pass2.csv from pass1.csv and Unicode/*.txt
    # Reads CNS codes from tmp/pass1.csv, finds their corresponding Unicode codepoint and character
    # from data/Unicode/*.txt files. Saves CNS code, Unicode codepoint (hex), and character to tmp/pass2.csv.
    pass2_path = 'tmp/pass2.csv'
    unicode_files_pattern = 'data/Unicode/*.txt'
    cns_to_unicode_info = {} # { 'CNS-CODE': ('UNICODE_HEX', 'CHARACTER'), ... }

    unicode_files_found = glob.glob(unicode_files_pattern)
    if not unicode_files_found:
        print(f"Error: No Unicode files found matching {unicode_files_pattern}")
        return

    for filepath in unicode_files_found:
        try:
            with open(filepath, 'r', encoding='utf-8') as infile:
                for line in infile:
                    parts = line.strip().split('\t')
                    if len(parts) >= 2:
                        cns_code = parts[0]
                        unicode_hex = parts[1]
                        try:
                            unicode_dec = int(unicode_hex, 16)
                            cns_to_unicode_info[cns_code] = (unicode_hex, chr(unicode_dec))
                        except ValueError:
                            print(f"Warning: Could not convert Unicode hex '{unicode_hex}' from {filepath} for {cns_code}")
                            cns_to_unicode_info[cns_code] = (unicode_hex, '') # Store empty char on error
        except FileNotFoundError:
            print(f"Error: {filepath} not found.")
            return

    processed_count_pass2 = 0
    try:
        with open(pass1_path, 'r', encoding='utf-8') as infile_pass1, \
             open(pass2_path, 'w', encoding='utf-8') as outfile_pass2:
            for line in infile_pass1:
                cns_code = line.strip()
                if cns_code in cns_codes_to_process: # Ensure it's one of the '常用' codes
                    unicode_hex, char = cns_to_unicode_info.get(cns_code, ('', ''))
                    if char: # Only write if a valid character was found
                        outfile_pass2.write(f"{cns_code}\t{unicode_hex}\t{char}\n")
                        processed_count_pass2 += 1
                    else:
                        print(f"Warning: No valid Unicode character found for CNS code '{cns_code}'. Skipping in pass2.")
        print(f"Step 2 completed: {processed_count_pass2} entries saved to {pass2_path}")
    except FileNotFoundError:
        print(f"Error: {pass1_path} not found, cannot proceed with Step 2.")
        return

    # Step 3: Generate tmp/pass3.csv from pass2.csv and CNS_phonetic.txt
    # Reads data from tmp/pass2.csv, finds the phonetic initial for each CNS code
    # from data/CNS_phonetic.txt. Saves four columns: CNS code, Unicode hex, character, and phonetic initial to tmp/pass3.csv.
    pass3_path = 'tmp/pass3.csv'
    cns_phonetic_path = 'data/CNS_phonetic.txt'
    cns_to_phonetic_initials = {} # { 'CNS-CODE': ['PHONETIC_INITIAL1', 'PHONETIC_INITIAL2'], ... }
    loaded_phonetic = 0

    try:
        with open(cns_phonetic_path, 'r', encoding='utf-8') as infile:
            for line in infile:
                parts = line.strip().split('\t')
                if len(parts) >= 2:
                    cns_code = parts[0]
                    phonetic = parts[1]
                    # Keep only the first character of the phonetic
                    if cns_code not in cns_to_phonetic_initials:
                        cns_to_phonetic_initials[cns_code] = []
                    if phonetic:
                        cns_to_phonetic_initials[cns_code].append(phonetic[0])
                        loaded_phonetic += 1
        print(f"Loaded {loaded_phonetic} phonetic entries from {cns_phonetic_path}")
    except FileNotFoundError:
        print(f"Error: {cns_phonetic_path} not found. Cannot proceed with Step 3.")
        return

    processed_count_pass3 = 0
    try:
        with open(pass2_path, 'r', encoding='utf-8') as infile_pass2, \
             open(pass3_path, 'w', encoding='utf-8') as outfile_pass3:
            for line in infile_pass2:
                parts = line.strip().split('\t')
                if len(parts) >= 3:
                    cns_code = parts[0]
                    unicode_hex = parts[1]
                    char = parts[2]

                    phonetic_initials = cns_to_phonetic_initials.get(cns_code, [''])
                    # A CNS code might have multiple phonetic initials, write one line for each
                    for initial in phonetic_initials:
                        outfile_pass3.write(f"{cns_code}\t{unicode_hex}\t{char}\t{initial}\n")
                        processed_count_pass3 += 1
        print(f"Step 3 completed: {processed_count_pass3} entries saved to {pass3_path}")

    except FileNotFoundError:
        print(f"Error: {pass2_path} not found, cannot proceed with Step 3.")
        return

    # Step 4: Generate tmp/table.lua from pass3.csv
    # Reads data from tmp/pass3.csv, groups characters by their phonetic initial,
    # maps phonetic initials to keyboard keys, and generates a Lua table where keys are
    # keyboard keys and values are concatenated strings of unique characters using Lua's long string format.
    # concatenated strings of unique characters. Saves the Lua table to tmp/table.lua.
    lua_table_path = 'tmp/table.lua'
    keyboard_map_path = 'data/keyboard/standard.csv'
    phonetic_to_keyboard_key = {} # { 'ㄇ': 'A', ... }

    try:
        with open(keyboard_map_path, 'r', encoding='utf-8') as infile:
            for line in infile:
                parts = line.strip().split('\t')
                if len(parts) >= 2:
                    keyboard_key = parts[0]
                    phonetic_symbol = parts[1]
                    phonetic_to_keyboard_key[phonetic_symbol] = keyboard_key
        print(f"Loaded {len(phonetic_to_keyboard_key)} keyboard mappings from {keyboard_map_path}")
    except FileNotFoundError:
        print(f"Error: {keyboard_map_path} not found. Cannot proceed with Step 4.")
        return

    keyboard_key_char_lists = {} # { 'A': ['字1', '字2'], ... }

    try:
        with open(pass3_path, 'r', encoding='utf-8') as infile_pass3:
            for line in infile_pass3:
                parts = line.strip().split('\t')
                if len(parts) >= 4:
                    char = parts[2]
                    phonetic_initial = parts[3]
                    # Map phonetic initial to keyboard key
                    keyboard_key = phonetic_to_keyboard_key.get(phonetic_initial, '')
                    if keyboard_key and char: # Only process if both keyboard key and character exist
                        if keyboard_key not in keyboard_key_char_lists:
                            keyboard_key_char_lists[keyboard_key] = []
                        keyboard_key_char_lists[keyboard_key].append(char)

        with open(lua_table_path, 'w', encoding='utf-8') as outfile_lua:
            outfile_lua.write("return {\n")
            sorted_keyboard_keys = sorted(keyboard_key_char_lists.keys())
            for keyboard_key in sorted_keyboard_keys:
                unique_chars = []
                seen_chars = set()
                for char in keyboard_key_char_lists[keyboard_key]:
                    if char and char not in seen_chars: # Ensure character is not empty and unique
                        unique_chars.append(char)
                        seen_chars.add(char)

                char_string = "".join(unique_chars)
                # Get the corresponding phonetic symbol for the comment
                phonetic_symbol_for_comment = ""
                # Reverse lookup the phonetic symbol from keyboard_key_to_phonetic (or find it from the original mapping)
                for p_symbol, k_key in phonetic_to_keyboard_key.items():
                    if k_key == keyboard_key:
                        phonetic_symbol_for_comment = p_symbol
                        break

                # Use Lua long string format [=[...]=] and add comment
                outfile_lua.write(f"    ['{keyboard_key}'] = [=[{char_string}]=], -- {phonetic_symbol_for_comment}\n")
            outfile_lua.write("}\n")
        print(f"Step 4 completed: Lua table saved to {lua_table_path}")
    except FileNotFoundError:
        print(f"Error: {pass3_path} not found, cannot proceed with Step 4.")
        return


if __name__ == '__main__':
    main()
