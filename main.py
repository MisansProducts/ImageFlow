#Made by Alex

import os
import time
import re

#Main Function
def main():
    #Sort Function
    def natural_sort_key(s): #Sorting algorithm for numbers (1 to 1, 2 to 2, etc...instead of 1 to 1, 10 to 2, etc)
        return [int(c) if c.isdigit() else c for c in pattern.split(s)] #Parsers any integers it finds in the string then splits it by the numbers

    #Variables
    path = os.path.join(os.path.dirname(__file__), "temp\\") #File path
    pattern = re.compile('([0-9]+)') #Recognizes base 10 digits

    #Path error
    if os.path.isdir(path) == False:
        print(f"Cannot find {path}", "Creating a folder named \"temp\". Move unsorted pictures in here.\n", sep = "\n")
        os.mkdir(path) #Creates "temp" folder in the same directory
    
    #Name Input
    my_name = input("File name: ") + " "

    #Number Input
    try:
        i = int(input("Starting number: "))
    except:
        i = 1
        print("Input error...setting starting number to 1.")
    
    #Loop Start
    for filename in sorted(os.listdir(path), key = natural_sort_key):
        new_name = my_name + str(i) + ".png" #Renames each picture and changes file extension to PNG
        my_source = path + filename #Gets old file location
        my_dest = path + new_name #Gets new file location
        os.rename(my_source, my_dest) #Renames the old file to the new file
        print(f"Renamed {filename} to {new_name}")
        time.sleep(0.015)
        i += 1
    #Loop End
    else:
        print("All done!")
        input() #Does not automatically close
        quit()

#Execution Check
if __name__ == '__main__':
    main()