import sys
import xbmc
import xbmcvfs
import xbmcplugin
import xbmcgui
import xbmcaddon
import webbrowser
import os
import shutil
import json
import urllib.request

# Définir l'ID du plugin
addon_handle = int(sys.argv[1])
addon = xbmcaddon.Addon("popcorn.plugin.contents")

#--------------------------------
#
# A définir dans l'action du menu
#
# xbmc.executebuiltin('ActivateWindow(Videos,"plugin://plugin.video.monplugin?action=list&amp;category=internet",return)')
#
#---------------------------------

# Charger les ressources (contents ou categories) à partir d'un fichier JSON
def load_resources_from_json(file_path, file_path_local):
    """Charge les ressources depuis un fichier JSON."""
    try:
        if not file_path == None:
            file_path = xbmcvfs.translatePath(file_path)
            file_path_local = xbmcvfs.translatePath(file_path_local)
            
            # Créer le dossier cible si nécessaire
            destination_dir = os.path.dirname(file_path_local)
            if not os.path.exists(destination_dir):
                os.makedirs(destination_dir)

            # Vérifier si la source est une URL
            if file_path.startswith("http://") or file_path.startswith("https://"):
                # Télécharger le fichier depuis l'URL
                urllib.request.urlretrieve(file_path, file_path_local)
            else:
                if not os.path.exists(file_path):
                    xbmcgui.Dialog().notification("Erreur", f"Fichier JSON introuvable : {str(file_path)}", xbmcgui.NOTIFICATION_ERROR, 5000)
                    return []
        
                # Copier le fichier vers l'emplacement donné
                #if not file_path == file_path_local:
                shutil.copy(file_path, file_path_local)

        # Charger le fichier JSON local        
        with open(file_path_local, 'r', encoding='utf-8') as file:
            return json.load(file)

    except json.JSONDecodeError:
        xbmcgui.Dialog().notification("Erreur", "Le fichier JSON est invalide.", xbmcgui.NOTIFICATION_ERROR, 10000)
        return []
    except Exception as e:
        xbmcgui.Dialog().notification("Erreur", f"Erreur inattendue : {str(e)}", xbmcgui.NOTIFICATION_ERROR, 10000)
        return []
    
# si non trouvé dans le fichier settings.xml alors on utilise la conf par défaut du plugin
contents_file = addon.getSetting("contents_file_path") or "special://home/addons/popcorn.plugin.contents/resources/data/contents.json"
if contents_file:
    contents = load_resources_from_json(contents_file,"special://userdata/addon_data/popcorn.plugin.contents/resources/data/contents.json")
else:
    xbmcgui.Dialog().notification("Setting non récupéré", f"Pas de setting trouvé pour {contents_file}", xbmcgui.NOTIFICATION_INFO, 3000)

# si non trouvé dans le fichier settings.xml alors on utilise la conf par défaut du plugin
categories_file = addon.getSetting("categories_file_path") or "special://home/addons/popcorn.plugin.contents/resources/data/categories.json"
if categories_file:
    categories = load_resources_from_json(categories_file,"special://userdata/addon_data/popcorn.plugin.contents/resources/data/categories.json")
else:
    xbmcgui.Dialog().notification("Setting non récupéré", f"Pas de setting trouvé pour {categories_file}", xbmcgui.NOTIFICATION_INFO, 3000)

background_path=None

def is_valid_category(category_name):
    """Vérifie si une catégorie est valide."""
    for category in categories:
        if category["category"] == category_name:
            return True
    return False


def get_category_details(category_name):
    """Récupère les détails d'une catégorie."""
    for category in categories:
        if category["category"] == category_name:
            return category
    return None


def list_contents(filter_category=None):
    """Affiche la liste des ressources, filtrées par catégorie si spécifié."""
    try:
        if filter_category:
            
            if not is_valid_category(filter_category):
                xbmcgui.Dialog().notification("Erreur", f"Catégorie invalide : {filter_category}", xbmcgui.NOTIFICATION_ERROR, 3000)
                return
            else:
                # Récupération des détails de la catégorie
                category_details = get_category_details(filter_category)
                
                if category_details and "background" in category_details:
                    background_path = xbmcvfs.translatePath(category_details['background'])

                if not background_path:
                    background_path = xbmcvfs.translatePath(addon.getAddonInfo('fanart'))                

            # Définir le contenu comme des vidéos
            xbmcplugin.setContent(addon_handle, "videos")
            
            filtered_contents = contents if filter_category is None else [res for res in contents if res.get("category") == filter_category]
            for content in filtered_contents:
                list_item = xbmcgui.ListItem(label=content['title'])
                list_item.setArt({'icon': content['image']})
                list_item.setArt({'thumb': content['image']})
                list_item.setArt({'fanart': background_path})

                if content["type"] == "link":
                    """on ouvre avec l'explorateur"""
                    url = f"{sys.argv[0]}?action=open&type={content['type']}&package={content['package']}&intent={content['intent']}&dataURI={content['dataURI']}"
                elif content["type"] == "music":
                    url = f"{sys.argv[0]}?action=open&type={content['type']}&dataURI={content['dataURI']}"
                elif content["type"] == "file":
                    url = f"{sys.argv[0]}?action=open&type={content['type']}&dataURI={content['dataURI']}"
                elif content["type"] == "application":
                    url = f"{sys.argv[0]}?action=open&type={content['type']}&package={content['package']}"

                info_tag = list_item.getVideoInfoTag()
                info_tag.setMediaType('movie')
                info_tag.setTitle(content['title'])
                info_tag.setPlot(content['description'])
                info_tag.setGenres([content['type']])
                
                xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=list_item, isFolder=False)
                xbmc.executebuiltin('Container.SetViewMode(55)')

            xbmcplugin.endOfDirectory(addon_handle)

    except Exception as e:
        xbmcgui.Dialog().notification("Erreur", f"Erreur lors de l'affichage des ressources : {str(e)}", xbmcgui.NOTIFICATION_ERROR, 3000)


def launch_android_app(package, intent=None, dataURI=None):
    """Lance une application Android via StartAndroidActivity."""
    try:
        if intent:
            if dataURI:
                xbmc.executebuiltin(f"StartAndroidActivity({package},{intent},,{dataURI})")
            else:
                xbmc.executebuiltin(f"StartAndroidActivity({package},{intent})")
        else:
            xbmc.executebuiltin(f"StartAndroidActivity({package})")
        xbmcgui.Dialog().notification("Lancement", f"StartAndroidActivity({package},{intent},,{dataURI})", xbmcgui.NOTIFICATION_INFO, 3000)
    except Exception as e:
        xbmcgui.Dialog().notification("Erreur", f"Impossible de faire un StartAndroidActivity : {str(e)}", xbmcgui.NOTIFICATION_ERROR, 3000)


def play_music(dataURI):
    """Joue un flux radio."""
    try:
        if dataURI:
            xbmc.Player().play(dataURI)
        else:
            xbmcgui.Dialog().notification("Erreur", "Adresse de la radio non définie.", xbmcgui.NOTIFICATION_ERROR, 3000)
    except Exception as e:
        xbmcgui.Dialog().notification("Erreur", f"Impossible de jouer la radio : {str(e)}", xbmcgui.NOTIFICATION_ERROR, 3000)



def open_file(package, intent=None, dataURI=None):
    """Ouvre un fichier parmi ces types:
        Image files (.JPEG, .PNG, .GIF, .TIFF, .BMP)
        Video files (WebM, .MPEG4, .3GPP, .MOV, .AVI, .MPEGPS, .WMV, .FLV)
        Text files (.TXT)
        Markup/Code (.CSS, .HTML, .PHP, .C, .CPP, .H, .HPP, .JS)
        Microsoft Word (.DOC and .DOCX)
        Microsoft Excel (.XLS and .XLSX)
        Microsoft PowerPoint (.PPT and .PPTX)
        Adobe Portable Document Format (.PDF)
        Apple Pages (.PAGES)
        Adobe Illustrator (.AI)
        Adobe Photoshop (.PSD)
        Tagged Image File Format (.TIFF)
        Autodesk AutoCad (.DXF)
        Scalable Vector Graphics (.SVG)
        PostScript (.EPS, .PS)
        TrueType (.TTF)
        XML Paper Specification (.XPS)
        Archive file types (.ZIP and .RAR)."""
    url = f"http://docs.google.com/viewer?url={dataURI}&embedded=true"
    launch_android_app({package}, {intent}, url)



def router(paramstring):
    """Route les actions en fonction des paramètres."""
    import urllib.parse
    
    params = dict(urllib.parse.parse_qsl(paramstring))
    action = params.get("action")
    resource_type = params.get("type")
    resource_category = params.get("category")
    
    if action == "open":
        if resource_type == "link":
            launch_android_app(params["package"], params["intent"], params["dataURI"])
        elif resource_type == "music":
            play_music(params["dataURI"])
        elif resource_type == "file":
            open_file(params["package"], params["intent"], params["dataURI"])
        elif resource_type == "application":
            launch_android_app(params["package"])
    elif action == "list" and resource_category:
        list_contents(filter_category=resource_category)
    else:
        list_contents(filter_category=None)

if __name__ == "__main__":
    router(sys.argv[2][1:])


