#include <iostream>
#include <Windows.h>
#include <vector>
#include <curl/curl.h>
#include <string>
#include <opencv4/opencv2/opencv.hpp>

int screenWidth = GetSystemMetrics(SM_CXSCREEN);
int screenHeight = GetSystemMetrics(SM_CYSCREEN);

//retrieves current screen data and puts it in the input array
bool getScreenData(std::vector<BYTE>& pixelData) {
    //retrieve device context for the entire screen
    HDC hdcScreen = GetDC(NULL);
    if (!hdcScreen) return false;

    //create a compatible device context
    HDC hdcMem = CreateCompatibleDC(hdcScreen);
    if (!hdcMem) {
        ReleaseDC(NULL, hdcScreen);
        return false;
    }

    //create a bitmap to hold the screenshot
    HBITMAP hBitmap = CreateCompatibleBitmap(hdcScreen, screenWidth, screenHeight);
    if (!hBitmap) {
        DeleteDC(hdcMem);
        ReleaseDC(NULL, hdcScreen);
        return false;
    }

    //select the bitmap into the memory DC
    HBITMAP holdBitmap = (HBITMAP)SelectObject(hdcMem, hBitmap);

    //copy screenshot to the memory DC
    BitBlt(hdcMem, 0, 0, screenWidth, screenHeight, hdcScreen, 0, 0, SRCCOPY);

    //get bitmap info
    BITMAPINFOHEADER bi = { sizeof(BITMAPINFOHEADER), screenWidth, -screenHeight, 1, 32, BI_RGB, 0, 0, 0, 0, 0 };
    //copies from memory DC to the array pixelData
    GetDIBits(hdcMem, hBitmap, 0, screenHeight, pixelData.data(), (BITMAPINFO*)&bi, DIB_RGB_COLORS);

    //cleans up
    SelectObject(hdcMem, holdBitmap);
    DeleteObject(hBitmap);
    DeleteDC(hdcMem);
    ReleaseDC(NULL, hdcScreen);

    return true;
}

//callback function to handle response data
size_t WriteCallback(void* contents, size_t size, size_t nmemb, std::string* output) {
    size_t total_size = size * nmemb;
    output->append((char*)contents, total_size);
    return total_size;
}

//sends HTTP get request the local LED strip controller
void writeToPage(int& dominantR, int& dominantG, int& dominantB) {
    CURL* curl;
    CURLcode res;
    std::string response;

    std::string r = std::to_string(dominantR);
    std::string g = std::to_string(dominantG);
    std::string b = std::to_string(dominantB);

    std::string urlString = "http://192.168.2.68/?mode=dc&red=" + std::to_string(dominantR) + "&green=" + std::to_string(dominantG) + "&blue=" + std::to_string(dominantB) + "&white=0&period=1000";
    const char* url = urlString.c_str();
    curl = curl_easy_init();

    if (curl) {
        curl_easy_setopt(curl, CURLOPT_URL, url);
        curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, WriteCallback);
        curl_easy_setopt(curl, CURLOPT_WRITEDATA, &response);
        curl_easy_setopt(curl, CURLOPT_TIMEOUT, 10L);

        res = curl_easy_perform(curl);

        if (res == CURLE_OK) {
            std::cout << "success" << std::endl;
        }
        else {
            std::cerr << "curl error: " << curl_easy_strerror(res) << std::endl;
        }

        curl_easy_cleanup(curl);
    }
}

//test function to display contents of pixelData
//used to confirm functionality of getScreenData()
void displayScreen(std::vector<BYTE>& pixelData) {
    cv::Mat rgba_image(screenHeight, screenWidth, CV_8UC4, pixelData.data());

    cv::Mat downsampledImage;

    cv::resize(rgba_image, downsampledImage, cv::Size(screenWidth / 20, screenHeight / 20), 0, 0, cv::INTER_AREA);
    cv::namedWindow("thewindow", cv::WINDOW_NORMAL);
    cv::imshow("thewindow", downsampledImage);

    cv::waitKey(0);
}

//finds the dominant RGB value in pixelData using k-means clustering
void processAverages(std::vector<BYTE>& pixelData, int& dominantR, int& dominantG, int& dominantB, cv::Mat& oldData) {
    //use pixelData to create an OpenCV Mat
    cv::Mat image(screenHeight, screenWidth, CV_8UC4, pixelData.data());
    cv::Mat downsampledImage;
    cv::resize(image, downsampledImage, cv::Size(screenWidth/20, screenHeight/20), 0, 0, cv::INTER_AREA);
    cv::Mat data = downsampledImage.reshape(1, downsampledImage.total());
    data.convertTo(data, CV_32F);

    //compare current screen data and old screen data
    //if they are identical, there's no need to change the LED color, so return;
    cv::Mat diff;
    cv::absdiff(data, oldData, diff); // Calculate absolute difference
    cv::Scalar sum_diff = cv::sum(diff); // Sum all elements in the difference matrix
    // If all channels of the sum are zero, the matrices are identical
    if (sum_diff[0] == 0 && sum_diff[1] == 0 && sum_diff[2] == 0 && sum_diff[3] == 0){
        return;
    }

    //saves current screen data as old screen data
    oldData = data.clone();

    std::vector<int> labels; //stores which cluster each data point belongs to
    cv::Mat centers; //stores the centers of the clusters

    int numClusters = 12;

    //apply K-Means clustering
    cv::kmeans(data, numClusters, labels, cv::TermCriteria(cv::TermCriteria::EPS + cv::TermCriteria::MAX_ITER, 10, 1.0),1, cv::KMEANS_PP_CENTERS, centers);

    //find the largest cluster
    std::vector<int> clusterCounts(numClusters, 0);
    for (int label : labels) {
        clusterCounts[label]++;
    }
    int dominantClusterIndex = 0;
    int maxCount = 0;
    for (int i = 0; i < numClusters; ++i) {
        if (clusterCounts[i] > maxCount) {
            maxCount = clusterCounts[i];
            dominantClusterIndex = i;
        }
    }

    //find the centroid of the dominant cluster
    cv::Vec3b dominantColor(static_cast<uchar>(centers.at<float>(dominantClusterIndex, 0)),
        static_cast<uchar>(centers.at<float>(dominantClusterIndex, 1)),
        static_cast<uchar>(centers.at<float>(dominantClusterIndex, 2)));

    dominantB = (int)dominantColor[0];
    dominantG = (int)dominantColor[1];
    dominantR = (int)dominantColor[2];
}


int main()
{
    curl_global_init(CURL_GLOBAL_DEFAULT);

    int dominantR, dominantG, dominantB; //current dominant RGB values

    //RGB values sent to LED strip
    int appliedR = 0;
    int appliedG = 0;
    int appliedB = 0;

    //former dominant RGB values
    int oldR = 0;
    int oldG = 0;
    int oldB = 0;
    
    std::vector<BYTE> pixelData(screenWidth * screenHeight * 4); //stores screen data

    std::vector<BYTE> old_data(screenWidth * screenHeight * 4); //oldData is used to check if the screen has changed since we last called the functions
    cv::Mat oldData(screenHeight, screenWidth, CV_8UC4, old_data.data());
    cv::resize(oldData, oldData, cv::Size(screenWidth / 20, screenHeight / 20), 0, 0, cv::INTER_AREA);
    oldData = oldData.reshape(1, oldData.total());
    oldData.convertTo(oldData, CV_32F);
    
    while (true) {
        getScreenData(pixelData);
        processAverages(pixelData, dominantR, dominantG, dominantB,oldData);
        
        //selects new RGB value of LED strip as a weighted average of the current dominant color, old dominant color, and old applied color
        appliedR = (dominantR * 2 + oldR + appliedR) / 4;
        appliedB = (dominantB * 2 + oldB + appliedB) / 4;
        appliedG = (dominantG * 2 + oldG + appliedG) / 4;

        oldR = appliedR;
        oldB = appliedB;
        oldG = appliedG;

        std::cout << appliedR << " " << appliedG << " " << appliedB << std::endl;
        writeToPage(appliedR, appliedG, appliedB);
        if (GetAsyncKeyState('A') & 0x8000) {
            std::cout << "ending program" << std::endl;
            break;
        }
    }

    curl_global_cleanup();
    return 0;
}
