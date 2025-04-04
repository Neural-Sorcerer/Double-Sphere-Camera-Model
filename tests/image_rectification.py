import cv2

from dscamera import DSCamera


if __name__ == "__main__":
    image_path = f"assets/images/sample.jpg"
    json_path = f"assets/jsons/calibration.json"
    
    # Load camera and image
    cam = DSCamera(json_path)
    img = cv2.imread(image_path)
    
    # Image rectification
    perspective = cam.to_perspective(img)
    equirectangular = cam.to_equirect(img)

    # Display
    cv2.imshow("Fisheye", img)
    cv2.imshow("Perspective", perspective)
    cv2.imshow("Equirectangular", equirectangular)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
