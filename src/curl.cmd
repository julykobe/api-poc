curl -H "BucketName: test" localhost:8000  -X PUT
curl -H "BucketName: test" http://localhost:8000/1.jpg  -X PUT --data-binary "@/Users/sunm/Downloads/DSC_0002.JPG"
