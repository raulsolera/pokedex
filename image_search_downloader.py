# import the necessary packages
import requests
import argparse
from requests import exceptions
import os
import cv2

# constants
SEARCH_URL = "https://api.cognitive.microsoft.com/bing/v7.0/images/search"

# when attempting to download images from the web both the Python
# programming language and the requests library have a number of
# exceptions that can be thrown so let's build a list of them now
# so we can filter on them
EXCEPTIONS = set([IOError, FileNotFoundError,
                  exceptions.RequestException, exceptions.HTTPError,
                  exceptions.ConnectionError, exceptions.Timeout])

def img_search_downloader(search_term, directory, max_results, group_size, apikey):
    """
    Launch search for search_term up to max_results images
    and save them in directory
    """
    headers = {"Ocp-Apim-Subscription-Key" : apikey}
    params  = {"q": search_term, "offset": 0, "count": group_size}
    response = requests.get(SEARCH_URL, headers=headers, params=params)
    response.raise_for_status()
    search_results = response.json()

    # grab the results from the search, including the total number of
    # estimated results returned by the Bing API
    estNumResults = min(search_results["totalEstimatedMatches"], max_results)
    print("[INFO] {} total results for '{}'".format(estNumResults,search_term))

    # initialize the total number of images downloaded thus far
    total = 0
    
    # loop over the estimated number of results in `GROUP_SIZE` groups
    for offset in range(0, estNumResults, group_size):

        # update the search parameters using the current offset, then
        # make the request to fetch the results
        print("[INFO] making request for group {}-{} of {}...".format(
            offset, offset + group_size, estNumResults))
        params["offset"] = offset
        search = requests.get(SEARCH_URL, headers=headers, params=params)
        search.raise_for_status()
        search_results = search.json()
        print("[INFO] saving images for group {}-{} of {}...".format(
            offset, offset + group_size, estNumResults))
            # loop over the results            

        for v in search_results["value"]:

            # try to download the image
            try:
                # make a request to download the image
                # print("[INFO] fetching: {}".format(v["contentUrl"]))
                r = requests.get(v["contentUrl"], timeout=30)

                # build the path to the output image
                ext = v["contentUrl"][v["contentUrl"].rfind("."):]
                p = os.path.sep.join([directory, "{}{}".format(str(total).zfill(8), ext)])

                # write the image to disk
                f = open(p, "wb")
                f.write(r.content)
                f.close()

            # catch any errors that would not unable us to download the
            # image
            except Exception as e:
                # check to see if our exception is in our list of
                # exceptions to check for
                if type(e) in EXCEPTIONS:
                    print("[INFO] skipping: {}".format(v["contentUrl"]))
                continue
                    
            # try to load the image from disk
            image = cv2.imread(p)

            # if the image is `None` then we could not properly load the
            # image from disk (so it should be ignored)
            if image is None:
                print("[INFO] deleting: {}".format(p))
                os.remove(p)
                continue

            # update the counter
            total += 1
            
            
def main():
    
    # construct the argument parser and parse the arguments
    ap = argparse.ArgumentParser()
    ap.add_argument("-d", "--directory", required=True,
                    help="Directory to save images into")
    ap.add_argument("-m", "--max_results", required=True, type=int,
                    help="Max results to search for")
    ap.add_argument("-f", "--file", required=True,
                    help="File for search terms")  
    ap.add_argument("-k", "--apikey", required=True,
                    help="Bing API key")  
    args = vars(ap.parse_args())

    # search terms
    search_terms = [line.rstrip('\n') for line in open(args['file'])]    
    
    # call search function
    for search_term in search_terms:
        directory = "/".join([args['directory'], search_term])
        if not os.path.exists(directory):
            os.makedirs(directory)
        img_search_downloader(search_term, directory,
                              args["max_results"],
                              min(50, args["max_results"]),
                              args["apikey"])      
    
if __name__ == "__main__":
    main()