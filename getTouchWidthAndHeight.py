# Test script for parsing report for invalid touch/objects on the screen
# Author M R Dennison
# 21 Apr 2021

import usb.core     # Core USB features.
import usb.util     # USB utility functions.
import argparse     # Parser for command-line options, arguments and sub-commands.
import sys          # System-specific parameters and functions
import os           # Provides functions for interacting with the operating system
import traceback    # Provide information about the runtime error

# Provides mechanism to use signal handlers
from signal import signal, SIGINT

#For producing colored terminal text and cursor positioning
from colorama import Fore, Back, Style

sys.dont_write_bytecode = True  # Do not write .pyc or .pyo files on the import of source modules.

# Convert the specified value into int 
def auto_int(x):
    return int(x, 0)

# Cat SIGINT or CTRL-C
def handler(signal_received, frame):
    # Handle any cleanup here
    print("")
    print(Fore.MAGENTA + 'SIGINT or CTRL-C detected. Exiting gracefully')
    print("Releasing interface previously claimed interface " + str(bIntNum) + "..."),
    try:
        usb.util.release_interface(dev, interface)
        print("Done.")
    except:
        print(Fore.RED + "Failed to release interface " + str(bIntNum) + "!")
        traceback.print_exc()
    if os.name != 'nt':
        print("Re-attaching kernel driver of interface " + str(bIntNum) + "..."),
        try:
            dev.attach_kernel_driver(bIntNum)
            print("Done.")   
        except:
            print(Fore.RED + "Failed to re-attach interface " + str(bIntNum) + "!")
            traceback.print_exc()
    print(Style.RESET_ALL)
    exit(0)

# Main
if __name__ == '__main__':
    #Tell Python to run the handler() function SIGINT is received
    signal(SIGINT, handler)

    # Avoiding UnicodeDecodeError
    if sys.version_info[0] < 3 and sys.getdefaultencoding() != 'utf-8':
        stdin, stdout, stderr = sys.stdin, sys.stdout, sys.stderr                                 
        # The magic trick that enables us to call setdefaultencoding()
        reload(sys)
        sys.stdin, sys.stdout, sys.stderr = stdin, stdout, stderr                                
        sys.setdefaultencoding(os.environ.get('PYTHONIOENCODING', 'utf-8'))

    # Initialise arg parser
    argparser = argparse.ArgumentParser(
        description="Get FW version number."
    )

    # Positional/Optional parameters
    argparser.add_argument('--vid', help="Vendor ID", type=auto_int)
    argparser.add_argument('--pid', help="Product ID", type=auto_int)

    # Handle no arguments call
    if len(sys.argv) < 2:
        argparser.print_usage()
        sys.exit(1)    # Parse the arguments
    
    args = argparser.parse_args()
    
    # Find device
    dev = usb.core.find(idVendor=args.vid, idProduct=args.pid)

    # Was it found?
    if dev is None:
        raise ValueError('Device not found')
    
    print("Found " + dev.product +  " from " + dev.manufacturer + ".")

    # Target Interface 
    bIntNum = 0;

    if os.name != 'nt':
        # Determine if a kernel driver is active on an interface.
        # If a kernel driver is active, you cannot claim the interface, and the backend will be unable to perform I/O.
        if dev.is_kernel_driver_active(bIntNum):
            print("Kernel driver is active.")
            print("Detaching kernel driver of " + str(bIntNum) + "...")
            dev.detach_kernel_driver(bIntNum)
    
    # The configuration parameter is the bConfigurationValue field of the configuration you want to set as active
    # If you call this method without parameter, it will use the first configuration found.
    try:
        if os.name == 'nt':
            print("Setting active configuration...")
            dev.set_configuration()
            print ("Configuration set.")
    except Exception as e:
        print ("Configuration not set.")
        traceback.print_exc()
    
    # Get the current active configuration of the device
    cfg = dev.get_active_configuration()
    
    # Print all the interfaces in the current active configuration
    print("Printing all the interfaces of the current active configuration")
    for interface in cfg:
        print(str(interface))
    print("-------------------------------------------")

    # Set the correct Interface (Interface #0)
    interface = cfg[(0, 0)]

    # Explicitly claim an interface
    # Users normally do not have to worry about interface claiming,
    # as the library takes care of it automatically. But there are situations
    # where you need deterministic interface claiming. For these uncommon
    # cases, you can use claim_interface.
    # If the interface is already claimed, either through a previously call
    # to claim_interface or internally by the device object, nothing happens.    
    print("Trying to claim device...")
    try:
        usb.util.claim_interface(dev, interface)
        print("Claimed device.")
    except usb.core.USBError as e:
        print("Error occurred claiming ")
        traceback.print_exc()

    # Get the OUT descriptor
    outPoint = usb.util.find_descriptor(
        interface,
        # match our first out endpoint
        custom_match= \
            lambda e: \
                usb.util.endpoint_direction(e.bEndpointAddress) == \
                usb.util.ENDPOINT_OUT)

    # get the IN descriptor
    inPoint = usb.util.find_descriptor(
        interface,
        # match our first in endpoint
        custom_match= \
            lambda e: \
                usb.util.endpoint_direction(e.bEndpointAddress) == \
                usb.util.ENDPOINT_IN)

    assert inPoint, outPoint is not None

    # Read data from the endpoint.
    # This method is used to receive data from the device. 
    # The endpoint parameter corresponds to the bEndpointAddress member whose endpoint you want to communicate with. 
    # The size_or_buffer parameter either tells how many bytes you want to read 
    # or supplies the buffer to receive the data (it must be an object of the type array).
    # The timeout is specified in miliseconds.
    # If the size_or_buffer parameter is the number of bytes to read, the method returns an array object with the data read. 
    # If the size_or_buffer parameter is an array object, it returns the number of bytes actually read.
    
    ret = None
    while True:
        try: 
            ret = inPoint.read(inPoint.wMaxPacketSize)       
            hex_ret = ['{:02X}'.format(0x00)] * inPoint.wMaxPacketSize
            print("Received " + str(len(ret)) + " bytes from bEndpointAddress " + hex(inPoint.bEndpointAddress) + "...")
            for i in range(len(ret)):
                hex_ret[i] = '{:02X}'.format(ret[i])
                if((ret[i] == 0x40  or ret[i] == 0xC0) and i <= 46):
                    if(ret[i] == 0x40):
                        print(Fore.RED + "Palm is detected"),
                    elif(ret[i] == 0xC0):
                        print(Fore.RED + "Foreign Object is detected"), 
                    else:
                        print("Valid touch")
                    x = i
                    touchReport =  ['{:02X}'.format(ret[x]) for x in range(x+9)]
                    print("Raw Touch Report: " + str(touchReport))
                    x = ret[i+1] + (ret[i+2] << 8)
                    y = ret[i+3] + (ret[i+4] << 8)
                    w = ret[i+5] + (ret[i+6] << 8)
                    h = ret[i+7] + (ret[i+8] << 8)
                    print("Location: " + str(x) + ", " + str(y))
                    print("Size    : " + str(w * 0.095) + "mm, " + str(h * 0.022) + "mm"),                 
                    print(Style.RESET_ALL)
            print(str(hex_ret))
        #except EOFError:    # Catch Ctrl-D
        #    break
        except usb.core.USBError as e:
            ret = None
            #if e.args == ('Operation timed out', ):
            #    continue
            if ('Operation timed out') in e.args:
                print(Fore.YELLOW + "NAK - " + str(e.args[1])),
                print(Style.RESET_ALL)
                continue
