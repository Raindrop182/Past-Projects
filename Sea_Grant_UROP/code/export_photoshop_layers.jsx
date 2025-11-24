/**
 * Exports twelve files, six TIFFs and six JPGs
 * 
 * Make sure all your layer names match the layer names in this file.
 * If not, an error will pop up and any files involving the misnamed layer will not be exported.
 * Note: this script also assumes all the layers in the right order as described in the image processing manual
 * (the lands+clouds is on top, and each matlab layer is above its respective seadas layer)
 * 
 * Edit the file paths below to match yours
 * 
 * To run the script, open your psd file, and go to File->Scripts
 */

//Define the paths
var outputFolder = Folder("F:/Processing/BATCH_09_28_2025/Processing/cloudyPractice/test"); //edit this to be the path to your output folder
var date = "09_28_2025" //edit this to be the date that you want on the file names

if (!outputFolder.exists) outputFolder.create();

//TIFF export settings
var tiffOpts = new TiffSaveOptions();
tiffOpts.imageCompression = TIFFEncoding.NONE;
tiffOpts.alphaChannels = true;
tiffOpts.layers = true;
tiffOpts.embedColorProfile = true;

//JPG export settings
var jpgSaveOptions = new JPEGSaveOptions();
jpgSaveOptions.embedColorProfile = true;
jpgSaveOptions.formatOptions = FormatOptions.STANDARDBASELINE;
jpgSaveOptions.matte = MatteType.NONE;
jpgSaveOptions.quality = 1;

//selects the currently open .psd file as the one to be exported
if (app.documents.length > 0) {
    var doc = app.activeDocument;
}

//displays status message
function showStatus(message) {
    if (!this.statusWindow) {
        var win = new Window("palette", "Script Status", undefined, {closeButton: false});
        win.statusText = win.add("statictext", undefined, message, {multiline: true});
        win.statusText.preferredSize.width = 300;
        win.show();
        this.statusWindow = win;
    } else {
        this.statusWindow.statusText.text = message;
        this.statusWindow.update();
    }
}

//checks if a layer exists. if the layer exists, makes it visible
function layerExists(layerName){
    layerExists=false
    for (var i = 0; i < doc.layers.length; i++) {
        if(doc.layers[i].name==layerName){
            layerExists=true;
            doc.layers[i].visible=true;
            break;
        }
    }
    return layerExists;
}

/**
 * saves a tiff and jpg to outputFolder
 * @param {*} toBeExportedLayers Array of strings.
 *          The last string represents the name of the file to be exported, while the other strings represent the layer names.
 */
function exportTiffJpg(toBeExportedLayers){
    showStatus("exporting "+toBeExportedLayers[toBeExportedLayers.length-1]);

    //changes visibility of all layers to false to prepare for exporting
    for (var i = 0; i < doc.layers.length; i++) {
    doc.layers[i].visible = false;
    }
    //checks if each needed layer exists. if it exists, the layer is set to visible. if it doesn't exist, an error is raised.
    for(var i=0;i<toBeExportedLayers.length-1;i++){
        if(!layerExists(toBeExportedLayers[i])){
            alert("Error: could not find layer: "+toBeExportedLayers[i]);
            return "none";
        }
    }

    var tiffFile = File(outputFolder + toBeExportedLayers[toBeExportedLayers.length-1]+".tif");
    doc.saveAs(tiffFile, tiffOpts, true);

    var jpgFile = File(outputFolder + toBeExportedLayers[toBeExportedLayers.length-1]+".jpg");
    doc.saveAs(jpgFile, jpgSaveOptions, true, Extension.LOWERCASE);

    showStatus("Done!")
}

var exportList=[]
exportList.push(new Array("land+clouds","diatoms_stripe_corrected.tif","seadas_products_diatoms_hirata.tif","/"+date+"_diatoms"))
exportList.push(new Array("land+clouds","greenalgae_stripe_corrected.tif","seadas_products_greenalgae_hirata.tif","/"+date+"_greenalgae"))
exportList.push(new Array("land+clouds","seadas_products_chlor_a_gray_scale.tif","Layer 1","seadas_products_RGB.tif","/"+date+"_truecolor"))
exportList.push(new Array("land+clouds","chlor_a_oceancolor_stripe_corrected.tif","seadas_products_chlor_a_oceancolor.tif","/"+date+"_chlor_a"))
exportList.push(new Array("land+clouds","dinoflagellates_stripe_corrected.tif","seadas_products_dinoflagellates_hirata.tif","/"+date+"_dinoflagellates"))
exportList.push(new Array("land+clouds","prymnesiophytes_stripe_corrected.tif","seadas_products_prymnesiophytes_hirata.tif","/"+date+"_prymnesiophytes"))

for(var i=0;i<exportList.length;i++){
    exportTiffJpg(exportList[i])
}
