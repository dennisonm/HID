# Test script for finding HID devices
# Author M R Dennison
# 19 Jan 2021
import usb.core
import usb.util
import argparse
import sys

def auto_int(x):
    return int(x, 0)

if __name__ == '__main__':

    # Initialise the argument parser
    argparser = argparse.ArgumentParser(
        description="Find USB device"        
    )

    # Positional/Optional parameters
    argparser.add_argument('--vid', help="Vendor ID", type=auto_int)
    argparser.add_argument('--pid', help="Product ID", type=auto_int)

    # Handle no arguments call
    if len(sys.argv) < 2:
        argparser.print_usage()
        sys.exit(1)    # Parse the arguments
        
    # Parse the arguments
    args = argparser.parse_args()
    
    # Find our device
    dev = usb.core.find(idVendor=args.vid, idProduct=args.pid)
 
    # was it found?
    if dev is None:
        print("Device not found :(")
        dev = usb.core.find(find_all=True)
        print("Discovered the following devices")
        for interface in dev:
            sys.stdout.write('\tVID=' + hex(interface.idVendor) + ' PID=' + hex(interface.idProduct) + '\n')
        exit(1)
    
    print("Yeey! Found the device!")        
    
    exit(0)
