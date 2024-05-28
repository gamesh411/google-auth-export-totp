#!/usr/bin/env python3

import base64
import cv2
import urllib.parse
import sys

from pyzbar.pyzbar import decode

import migration_pb2  # generated protobuf binding
from google.protobuf.message import DecodeError


def decode_otpauth_migration_url(migration_url):
    # Extract the Base64-encoded data
    try:
        encoded_data = migration_url.split("data=")[1]
    except IndexError:
        raise ValueError("Invalid otpauth-migration URL format.")

    # Decode URL encoding
    encoded_data = urllib.parse.unquote(encoded_data)

    # Decode the Base64 data
    try:
        decoded_data = base64.urlsafe_b64decode(encoded_data + "==")
    except base64.binascii.Error as e:
        raise ValueError(f"Failed to decode base64 data: {e}")

    # Parse the protobuf message
    migration_payload = migration_pb2.MigrationPayload()
    try:
        migration_payload.ParseFromString(decoded_data)
    except DecodeError as e:
        raise ValueError(f"Failed to parse protobuf message: {e}")

    # Extract TOTP parameters and construct URLs
    totp_urls = []
    for otp_parameters in migration_payload.otp_parameters:
        issuer = otp_parameters.issuer
        account_name = otp_parameters.name
        secret = (
            base64.b32encode(otp_parameters.secret).decode("utf-8").replace("=", "")
        )
        algorithm = "SHA1"  # Assuming SHA1 as the default algorithm
        digits = otp_parameters.digits
        totp_url = f"otpauth://totp/{issuer}:{account_name}?secret={secret}&issuer={issuer}&algorithm={algorithm}&digits={digits}"
        totp_urls.append(totp_url)

    return totp_urls


def decode_qr_code(image_path):
    # Read the image
    image = cv2.imread(image_path)

    # Decode the QR code
    decoded_objects = decode(image)

    results = []
    # Print the results
    for obj in decoded_objects:
        results.append({"type": obj.type, "data": obj.data.decode("utf-8")})

    return results


def main():
    # Path to your image
    image_path = sys.argv[1]
    for qr_results in decode_qr_code(image_path):
        try:
            totp_urls = decode_otpauth_migration_url(qr_results["data"])
            for url in totp_urls:
                print(url)
        except ValueError as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()
