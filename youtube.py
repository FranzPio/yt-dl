from PyQt5 import QtCore
import pytube, pytube.exceptions
import urllib.request, urllib.error
import bs4
import sys
import collections.abc


# TODO: convert downloaded video files (e.g. mp4 to mp3)
class YouTube(QtCore.QObject):
    resolutions = collections.OrderedDict([("144p", "144p"), ("144p 15 fps", "144p15"), ("240p", "240p"),
                                           ("360p", "SD (360p)"), ("480p", "FWVGA (480p)"),
                                           ("720p", "HD (720p)"), ("720p HFR", "HD (720p60)"),
                                           ("1080p", "Full HD (1080p)"), ("1080p HFR", "Full HD (1080p60)"),
                                           ("1440p", "Quad HD (1440p)"), ("1440p HFR", "Quad HD (1440p60)"),
                                           ("2160p", "4K UHD (2160p)"), ("2160p HFR", "4K UHD (2160p60)"),
                                           ("2160p-2304p", "4K UHD (2160p-2304p)"),
                                           ("2160p-4320p", "4K UHD (2160p-4320p)")])

    formats = collections.OrderedDict([("mp4", "MPEG-4 AVC / H.264 (.mp4)"), ("webm", "VP9 (.webm)"),
                                       ("3gp", "MPEG-4 Visual (.3gp)"), ("flv", "Sorenson H.263 (.flv)")])

    standard_formats = collections.OrderedDict([("mp4", ["360p", "720p"]), ("webm", ["360p"]),
                                                ("3gp", ["144p", "240p"])])

    finished = QtCore.pyqtSignal()
    success = QtCore.pyqtSignal(list)
    error = QtCore.pyqtSignal(str, tuple)
    critical_error = QtCore.pyqtSignal(str, tuple)

    def __init__(self, page_url):
        super().__init__()
        self.page_url = page_url

    def find_videos(self):
        try:
            yt = pytube.YouTube(self.page_url)
            available_formats = yt.get_videos()
            videos = [{"index": 1, "title": yt.title, "url": yt.url, "formats": available_formats}]
            self.success.emit(videos)
            self.finished.emit()
            return
        except (ValueError, AttributeError, urllib.error.URLError, pytube.exceptions.PytubeError):
            try:
                yt = pytube.YouTube("https://" + self.page_url)
                available_formats = yt.get_videos()
                videos = [{"index": 1, "title": yt.title, "url": yt.url, "formats": available_formats}]
                self.success.emit(videos)
                self.finished.emit()
                return
            except (ValueError, AttributeError, urllib.error.URLError, pytube.exceptions.PytubeError):
                error = "Invalid url: no videos were found. Check url for typos."
                self.error.emit(error, sys.exc_info())
                self.finished.emit()
                return
            except pytube.exceptions.AgeRestricted:
                # the video could be age restricted OR we're maybe dealing with a playlist
                page_html = urllib.request.urlopen("https://" + self.page_url).read()
                page_soup = bs4.BeautifulSoup(page_html, "lxml")

                index = 1

                playlist_html = page_soup.find_all(
                    "a", attrs={"class": "pl-video-title-link yt-uix-tile-link yt-uix-sessionlink spf-link "})

                if not playlist_html:
                    error = "This video is age-restricted. It cannot be downloaded as this is not supported yet."
                    self.error.emit(error, sys.exc_info())
                    self.finished.emit()
                    return
                else:
                    videos = []
                    for a in playlist_html:
                        videos.append({"index": index, "title": a.string.strip(),
                                       "url": "https://www.youtube.com" + a.get("href")})
                        index += 1

                    self.success.emit(videos)
                    self.finished.emit()
                    return
        except (pytube.exceptions.CipherError, pytube.exceptions.ExtractorError):
            error = "An error occurred. Couldn't get video(s). Try another url."
            self.critical_error.emit(error, sys.exc_info())
            self.finished.emit()
            return
        except pytube.exceptions.AgeRestricted:
            # the video could be age restricted OR we're maybe dealing with a playlist

            page_html = urllib.request.urlopen(self.page_url).read()
            page_soup = bs4.BeautifulSoup(page_html, "lxml")

            index = 1

            playlist_html = page_soup.find_all(
                "a", attrs={"class": "pl-video-title-link yt-uix-tile-link yt-uix-sessionlink spf-link "})

            if not playlist_html:
                error = "This video is age-restricted. It cannot be downloaded as this is not supported yet."
                self.error.emit(error, sys.exc_info())
                self.finished.emit()
                return
            else:
                videos = []
                for a in playlist_html:
                    videos.append({"index": index, "title": a.string.strip(),
                                   "url": "https://www.youtube.com" + a.get("href")})
                    index += 1

                self.success.emit(videos)
                self.finished.emit()
                return

                # print("\nThere are ", len(available_formats), " video formats are available:\n", sep="")
                # for index, format in enumerate(available_formats):
                #     print(index, "-", format)
                # while True:
                #     print("\nNow choose your desired format.\n")
                #     print("extension (e.g. \"mp4\", \"3gp\", \"flv\", \"webm\"):")
                #     extension = input("> ")
                #     print("\nresolution (e.g. \"144p\", \"360p\", \"720p\"):")
                #     resolution = input("> ")
                #     try:
                #         video = yt.get(extension, resolution)
                #         break
                #     except pytube.exceptions.DoesNotExist:
                #         print("\n\033[31mNo videos met these criteria. Check the extension and resolution you entered.\033[0m")
                # print("\nYour video is being downloaded, please wait...")
                # video.download("")
                # print("\n-----------------------------------"
                #       "\nSuccessfully downloaded video.\n")

    @staticmethod
    def prettified(video_formats):
        format_dict = YouTube.formats
        resolution_dict = YouTube.resolutions

        if type(video_formats) in (collections.OrderedDict, dict):
            prettified_dict = collections.OrderedDict()
            for format, resolutions in video_formats.items():
                prettified_dict.update({format_dict[format]: []})
                for resolution in resolutions:
                    prettified_dict[format_dict[format]].append(resolution_dict[resolution])
            return prettified_dict

        elif type(video_formats) == str:
            if video_formats in format_dict.keys():
                return format_dict[video_formats]
            elif video_formats in resolution_dict.keys():
                return resolution_dict[video_formats]

        elif type(video_formats) in (list, tuple):
            prettified_list = []
            for format in video_formats:
                if format in format_dict.keys():
                    prettified_list.append(format_dict[format])
                elif format in resolution_dict.keys():
                    prettified_list.append(resolution_dict[format])
            return prettified_list

        else:
            return None

    @staticmethod
    def uglified(video_formats):
        reversed_format_dict = collections.OrderedDict((value, key) for key, value in YouTube.formats.items())
        reversed_resolution_dict = collections.OrderedDict((value, key) for key, value in YouTube.resolutions.items())

        if type(video_formats) in (collections.OrderedDict, dict):
            uglified_dict = collections.OrderedDict()
            for format, resolutions in video_formats.items():
                uglified_dict.update({reversed_format_dict[format]: []})
                for resolution in resolutions:
                    uglified_dict[reversed_format_dict[format]].append(reversed_resolution_dict[resolution])
            return uglified_dict

        elif type(video_formats) == str:
            if video_formats in reversed_format_dict.keys():
                return reversed_format_dict[video_formats]
            elif video_formats in reversed_resolution_dict.keys():
                return reversed_resolution_dict[video_formats]

        elif type(video_formats) in (list, tuple):
            uglified_list = []
            for format in video_formats:
                if format in reversed_format_dict.keys():
                    uglified_list.append(reversed_format_dict[format])
                elif format in reversed_resolution_dict.keys():
                    uglified_list.append(reversed_resolution_dict[format])
            return uglified_list

        else:
            return None

    @staticmethod
    def download_video(video, extension="mp4", resolution=None, destination=""):
        raise NotImplementedError("Since this application is still under active development, not all features are "
                                  "available yet. Be patient!")

    @staticmethod
    def download_playlist(video_list, extension="mp4", resolution=None, destination=""):
        raise NotImplementedError("Since this application is still under active development, not all features are "
                                  "available yet. Be patient!")

    @staticmethod
    def _download(video_list, extension="mp4", resolution=None, destination=""):
        # TODO: "really" do it (put downloading into thread, emit signals, update progress bar etc.)
        successful_downloads = 0
        errors = 0
        for video_info in video_list:
            print("Downloading", video_info["index"], "of", len(video_list), "...", flush=True)
            try:
                yt = pytube.YouTube(video_info["url"])
                video = yt.get(extension, resolution)
                video.download(destination)
            except pytube.exceptions.DoesNotExist:
                print("An error occurred:\nThe video isn't available in the given format / resolution."
                      "This happens due to a bug that will be fixed soon.\n", sys.exc_info())
                errors += 1
            except Exception:
                print("An error occurred:\n", sys.exc_info())
                errors += 1
            else:
                successful_downloads += 1

        print(successful_downloads, "of", len(video_list), "videos were downloaded successfully.")
        if errors:
            print(errors, "errors occurred.")
        return

        # print("\nThis appears to be a link to a playlist."
        #       "\nThere are ", len(video_list), " videos in it:\n", sep="")
        # time.sleep(2.5)
        # print("------------------------------")
        # for video in video_list:
        #     print(video["index"], ". ", video["title"], sep="")
        # print("------------------------------")
        # print("\nNow choose your desired format.\n"
        #       "If that format does not exist, an mp4 with the highest resolution available will be downloaded.\n")
        # print("extension (e.g. \"mp4\", \"3gp\", \"flv\", \"webm\"):")
        # extension = input("> ")
        # print("\nresolution (e.g. \"144p\", \"360p\", \"720p\"):")
        # resolution = input("> ")

        # error_list = []
        # os_error_list = []
        # age_restricted_list = []
        # successful_downloads = 0
        #
        # print("\n", len(video_list), " videos are being downloaded, please wait...\n", sep="")
        # print(successful_downloads, " / ", len(video_list), " downloaded successfully | ",
        #       len(error_list) + len(os_error_list) + len(age_restricted_list), " error(s) occurred",
        #       sep="", end="\r", flush=True)
        #
        # for video in video_list:
        #     try:
        #         yt = pytube.YouTube(video["url"])
        #         video = yt.get(extension, resolution)
        #         video.download(destination)
        #         successful_downloads += 1
        #     except pytube.exceptions.DoesNotExist:
        #         try:
        #             yt = pytube.YouTube(video["url"])
        #             video = yt.get(extension, resolution)
        #             video.download(destination)
        #             successful_downloads += 1
        #         except (pytube.exceptions.PytubeError, pytube.exceptions.CipherError, pytube.exceptions.ExtractorError):
        #             error_list.append(video)
        #             continue
        #     except (pytube.exceptions.PytubeError, pytube.exceptions.CipherError, pytube.exceptions.ExtractorError):
        #         error_list.append(video)
        #         continue
        #     except pytube.exceptions.AgeRestricted:
        #         age_restricted_list.append(video)
        #         continue
        #     except OSError:
        #         os_error_list.append(video)
        #         continue
        #     finally:
        #         #        (prints on the same line without flushing the old stuff / prints nothing)
        #         # print(successful_downloads, " / ", len(video_list), " downloaded successfully | ",
        #         #       len(error_list) + len(os_error_list) + len(age_restricted_list), " error(s) occurred",
        #         #       sep="", end="\r", flush=True)
        #         pass  # TODO: later some progress bar should be updated at this point
        #
        # print("\n-----------------------------------"
        #       "\nSuccessfully downloaded ", successful_downloads, " videos.\n", sep="")
        # if error_list:
        #     print(len(error_list), " video(s) couldn't be downloaded because an unexpected error occurred.\n", sep="")
        # if os_error_list:
        #     print(len(os_error_list), " video(s) couldn't be downloaded because\n"
        #                               "- the filename already exists\n"
        #                               "- you don't have write permission to the current working directory\n"
        #                               "- or some other weird OSError occurred\n", sep="")
        # if age_restricted_list:
        #     print(len(age_restricted_list), " video(s) couldn't be downloaded because of age restrictions.\n", sep="")


# def start():
#     print("Enter the YouTube url of a video or playlist to continue:\n")
#     return input("> ")
