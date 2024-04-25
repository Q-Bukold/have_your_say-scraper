# forked from https://github.com/felixrech/hys_scraper/tree/master
# own edits are marked by ##QB

import os
import re
import sys
import json
import time
import requests
import pandas as pd
from typing import List, Tuple

import pickle ##QB added this library

from initative_scraper import scrape_initatives


class HYS_Scraper_new:
    def __init__(
        self,
        publication_id: str,
        target_dir: str = None,
        download_attachments: bool = True,
        sleep_time: int = 1,
    ) -> None:
        """Scraper for the European Commission's 'Have your Say' plattform. Can scrape
        an initiative's feedbacks including file attachments, as well as the overall
        country and category statistics.

        The publication id is what comes after 'p_id=' in the initiative's URL. Take
        the AIAct's commission adoption as an example:
        URL: https://ec.europa.eu/info/law/better-regulation/have-your-say/initiatives/12527-Artificial-intelligence-ethical-and-legal-requirements/feedback_en?p_id=24212003
        Publication ID: 24212003

        Parameters
        ----------
        publication_id : str
            The publication id - what comes after 'p_id=' in the initiative's URL.
        target_dir : str, optional
            Directory to save the feedback and statistics dataframes to, by default
            creates a folder in the current working directory based on the publication's
            id and name.
        download_attachments : bool, optional
            Whether to download the feedbacks' attachments, by default True.
        sleep_time : int, optional
            Minimum time between requests to the 'Have your Say' plattform in seconds,
            by default 1s. If you are scraping large amounts of data, please set this
            to a reasonably high level to avoid causing harm to the 'Have your Say'
            plattform.
        """
        # Set up class attributes
        self.base_url = "https://ec.europa.eu/info/law/better-regulation/"
        # Time of last request to a ec.europa.eu, as seconds since 1970-01-01
        self.last_request = 0
        self.max_print = 0  # Required for deleting (and rewriting) line

        # Copy arguments into class attributes
        self.publication_id = publication_id
        self.sleep_time = sleep_time
        self.download_attachments = download_attachments
        
        # check if scraper has to start after connection error #QB added this
        config = json.load(open('./tmp/config.json'))
        continue_feedback_scrape = config["continue_feedback_scrape_after_error"]
        self.continue_feedback_scrape = bool(continue_feedback_scrape)
        print(f"INFO: continuing feedback scrape after connection error?: {str(self.continue_feedback_scrape)}")
     
        # set header for good practice ##QB added this
        headers = requests.utils.default_headers()
        headers['From'] = 'University of Hildesheim (bukold@uni-hildesheim.de)'
        self.headers = headers
        
        # If topic_dir is not specified, ...
        if target_dir is None:
            try:
                # Use publication id and pub. name to create folder in working dir.
                publication_name = self._snake_case(self.scrape_publication_name())
                target_dir = f"{publication_id}_{publication_name}/"
            except:
                # With just publication id as fallback
                target_dir = publication_id + "/"
        self.target_dir = target_dir

        # Try to create target directory, if it doesn't exist
        self._create_output_folder()

    def scrape(
        self, download_attachments: bool = None, save_dataframes: bool = True
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Scrape the initiative's feedback submissions and statistics.

        Parameters
        ----------
        download_attachments : bool, optional
            Overwrite the download_attachments specified when the scraper was
            initialized.
        save_dataframes : bool, optional
            Save the feedback and statistics dataframe, by default True.

        Returns
        -------
        tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]
            Feedback, by country statistics, and by category statistics dataframes.
        """
        feedbacks_df = self.scrape_feedbacks()

        if (download_attachments is None and self.download_attachments) or (
            download_attachments is not None and download_attachments
        ):
            try: #QB
                attachments_df = self._download_attachments(feedbacks_df)
                attachments_df.to_csv(f"{self.target_dir}/attachments.csv", index=False)
            except (ConnectionAbortedError, ConnectionError, ConnectionRefusedError, ConnectionResetError, ValueError) as e:
                self._change_config("continue_feedback_scrape_after_error", True)
                raise ValueError("Connection Error during Attachment Scrape")

        try: #QB
            country_df, category_df = self.scrape_statistics()
        except (ConnectionAbortedError, ConnectionError, ConnectionRefusedError, ConnectionResetError, ValueError) as e:
            self._change_config("continue_feedback_scrape_after_error", True)
            raise ValueError("Connection Error during Statistics Scrape")


        if save_dataframes:
            country_df.to_csv(f"{self.target_dir}countries.csv", index=False)
            category_df.to_csv(f"{self.target_dir}categories.csv", index=False)

            # Attachments column (each a list of strings) breaks csv
            csv_df = feedbacks_df.drop(columns="attachments")
            csv_df.to_csv(f"{self.target_dir}/feedbacks.csv", index=False)

        # if nothing failed, feedback backup is not nessesary #QB
        self._change_config("continue_feedback_scrape_after_error", False)
        return feedbacks_df, country_df, category_df

    def scrape_publication_name(self) -> str:
        """Scrape the name of the publication that the initiative belongs to.

        Returns
        -------
        str
            'Have your Say' internal publication name, e.g. "Requirements for Artificial
            Intelligence" for the AIAct's commission adoption (p_id 24212003).
        """
        url = (
            self.base_url
            + f"api/shortTitleByPublicationId?publicationId={self.publication_id}"
        )

        r = self._get(url)
        return json.loads(r)["shortTitle"]

    def scrape_feedbacks(self) -> pd.DataFrame:
        """Scrape the initiative's feedback submissions.

        Returns
        -------
        pd.DataFrame
            Feedback dataframe.
        """
        feedbacks = self._scrape_pages()
        return self._feedbacks_to_dataframe(feedbacks)

    def _scrape_page(self, page: int = 0, size: int = None) -> dict:
        """Scrape one page worth of feedback submissions.

        Parameters
        ----------
        page : int, optional
            Page number, zero-indexed, by default 0.
        size : int, optional
            Number of submissions per page, by default None (letting 'Have your Say'
            decide).

        Returns
        -------
        dict
            Parsed JSON return value.
        """
        url = self.base_url + f"api/allFeedback?publicationId={self.publication_id}"
        url += f"&page={page}"
        url += f"&size={size}" if size is not None else ""
        #"https://ec.europa.eu/info/law/better-regulation/api/allFeedback?publicationId=31234550&page=0"

        r = self._get(url)
        return json.loads(r)
            
    def _scrape_pages(self) -> List[dict]:
        """Scrape all the initiative's feedback submissions.

        Returns
        -------
        list[dict]
            List of dicts, each of which represents a single submission (parsed JSON
            from 'Have your Say' API).
        """
        self._update_print_line("Scraping the feedback:       [⏳]")

        # Access API to determine default page size and number of pages
        initial = self._scrape_page()
        size, n_pages = initial["page"]["size"], initial["page"]["totalPages"]

        ##QB added if clause and load from backup
        if self.continue_feedback_scrape == True:
            with open('./tmp/feedback_backup.pkl', 'rb') as f:
                feedbacks = pickle.load(f)
            start_page = len(feedbacks)/10 #to get from number of feedbacks to number of pages
            start_page = int(start_page)
        else:
            feedbacks = []
            start_page = 0
            
        
        for page in range(start_page, n_pages): #QB added skipping of already scraped feedbacks
            self._update_print_line(
                "Scraping feedback pages:       "
                + f"[{str(page+1).rjust(len(str(n_pages)))} of {n_pages} ⏳]",
            )
            try: ##QB added ConnectionError handling
                current = self._scrape_page(page, size=size)
                feedbacks += current["_embedded"]["feedback"]
                #raise ValueError('TestError')
            except (ConnectionAbortedError, ConnectionError, ConnectionRefusedError, ConnectionResetError, ValueError) as e:
                print(f"\nERROR: {e} during feedback-scraping of page {page}\nINFO: Saved scraped feedbacks in tmp/feedback_backup.pkl")
                self._feedback_backup(feedbacks)
                self._change_config("continue_feedback_scrape_after_error", True)             
                raise ValueError(f'Connection Error {e}')

   
        self._update_print_line("Scraping feedback:       [✔️ 🎉✨]", end=True)
        
        # feedback scrape ended without error, change config #QB added this
        self._change_config("continue_feedback_scrape_after_error", False)
        ##QB added this: Backup anyway, in case attachment scrape fails
        self._feedback_backup(feedbacks)
        
        return feedbacks

    def _feedbacks_to_dataframe(
        self, feedbacks: List[dict], comfort: bool = True
    ) -> pd.DataFrame:
        """Convert a list of feedback dictionaries into a Pandas DataFrame.

        Parameters
        ----------
        feedbacks : list[dict]
            List of feedbacks, generally from _scrape_pages.
        comfort : bool, optional
            Convert some of the values from 'SHOUTY' to 'normal' (i.e. lowercasing),
            snake_case the column names (by default camelCase) and parse the publication
            date, by default True.

        Returns
        -------
        pd.DataFrame
            DataFrame containing all feedback submissions.
        """
        # Convert list of feedback dicts to dataframe
        df = pd.DataFrame(feedbacks)

        # Drop some unnecessary columns
        df = df.drop(
            columns=["isMyFeedback", "historyEventOccurs", "_links"],
            errors="ignore",
        )

        # Convert attachments into list of download links
        attachment_api = "https://ec.europa.eu/info/law/better-regulation/api/download/"
        df["attachments"] = df["attachments"].map(
            lambda l: [attachment_api + str(x["documentId"]) for x in l]
        )

        if comfort:
            # Go from 'SHOUTY' to 'normal'
            lowercase_cols = {
                "language",
                "publication",
                "userType",
                "companySize",
                "publicationStatus",
                "governanceLevel",
                "scope",
            }
            for col in lowercase_cols & set(df.columns):
                df[col] = df[col].str.lower()

            # Snake case the column names
            df.columns = [self._snake_case(col) for col in df.columns]

            # Parse the publication date if the column exists
            if "date_feedback" in df.columns:
                df["date_feedback"] = pd.to_datetime(
                    df["date_feedback"], errors="coerce"
                )

        # Add empty attachments column if it doesn't exist
        if "attachments" not in df.columns:
            df["attachments"] = [[] for _ in range(len(df))]

        return df

    def _download_attachments(self, df: pd.DataFrame) -> pd.DataFrame:
        """Download the attachments to the feedback submissions.

        Parameters
        ----------
        df : pd.DataFrame
            DataFrame of feedback submissions. Has to contain the 'attachments' column.

        Returns
        -------
        pd.DataFrame
            DataFrame containing the filenames of the downloaded attachments (relative
            to target_dir).
        """
        tmp_location = "./.tmp.pdf"

        # Get a id, attachment dataframe
        df = df[["id", "attachments"]].copy()
        df = df.explode("attachments").dropna(subset=["attachments"])
        df = df.reset_index(drop=True)

        # Filename is feedback id.pdf and id_2.pdf, id_3.pdf for multiple attachments
        df["dup"] = df.groupby("id").cumcount() + 1
        df["dup"] = df["dup"].map(lambda x: f"_{x}" if x > 1 else "")
        df["filename"] = "attachments/" + df["id"].astype(str) + df["dup"] + ".pdf"

        skipped_attachments = 0
        for i, row in df.iterrows():
            self._update_print_line(
                "Downloading the attachments: "
                + f"[{str(i+1).rjust(len(str(len(df))))} of {len(df)} ⏳]",
            )

            filename = f"{self.target_dir}{row.filename}"

            # Skip download if file already exists
            if os.path.exists(filename):
                skipped_attachments += 1
                continue
            
            self._get_file(row.attachments, tmp_location)
            os.rename(tmp_location, filename)
            #raise ValueError("TestError")
                    
        self._update_print_line("Downloading the attachments: [✔️ 🎉✨]", end=True)
        if skipped_attachments > 0:
            print(
                f"({skipped_attachments} attachments were skipped, as they already "
                + "exist in the target directory)"
            )
        return df[["id", "filename"]]

    def scrape_statistics(
        self, comfort: bool = True
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Scrape the initiative statistics from 'Have your Say'.

        Parameters
        ----------
        comfort : bool, optional
            Whether to snake_case the user categories, by default True.

        Returns
        -------
        tuple[pd.DataFrame, pd.DataFrame]
            By country statistics and by category statistics dataframes.
        """
        self._update_print_line("Scraping the statistics:     [1 of 2 ⏳]")
        country_url = (
            self.base_url
            + f"brpapi/feedBackByCountry?publicationId={self.publication_id}"
        )
        countries = json.loads(self._get(country_url))
        country_df = pd.DataFrame(countries["feedbackCountryList"])
        country_df = country_df.rename(
            columns={"label": "country", "total": "n_responses"}
        )

        self._update_print_line("Scraping the statistics:     [2 of 2 ⏳]")
        category_url = (
            self.base_url
            + f"brpapi/feedbackByCategorOfRespondent?publicationId={self.publication_id}"
        )
        categories = json.loads(self._get(category_url))
        category_df = pd.DataFrame(data=categories.items(), index=categories.keys())
        category_df = category_df.rename(columns={0: "category", 1: "n_responses"})
        category_df = category_df.reset_index(drop=True)
        if comfort:
            category_df["category"] = category_df["category"].map(self._snake_case)
        self._update_print_line("Scraping the statistics:     [✔️ 🎉✨]", end=True)

        return country_df, category_df

    def _get(self, url: str, retries: int = 3) -> str:
        """HTTP GET given url.

        Parameters
        ----------
        url : str
            URL.
        retries : int, optional
            Number of retries, by default 3.

        Returns
        -------
        str
            Text returned by the server.

        Raises
        ------
        RuntimeError
            If the number of retries is exceeded.
        """
        self._sleep()

        r = requests.get(url, headers=self.headers) ##QB added Headers
        self.last_request = time.time()

        if r.status_code != 200:
            if retries > 0:
                return self._get(url, retries=retries - 1)
            raise RuntimeError(
                f"\nError while accessing {url} - status code: [{r.status_code}]"
            )

        return r.text

    def _get_file(self, url: str, target: str) -> None:
        """Download a (binary) file to given location.

        Parameters
        ----------
        url : str
            URL of the file to download.
        target : str
            Name of the file to save into.
        """
        self._sleep()

        pdf = requests.get(url, headers=self.headers, stream=True) ##QB added Headers
        with open(target, "wb") as f:
            for chunk in pdf.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)

        self.last_request = time.time()

    def _create_output_folder(self) -> None:
        """Create the target folder if it doesn't exist and do the same for the
        attachments folder inside the target_dir.
        """
        try:
            if not os.path.isdir(self.target_dir):
                os.mkdir(self.target_dir)

            attachment_dir = self.target_dir + "attachments/"
            if self.download_attachments and not os.path.isdir(attachment_dir):
                os.mkdir(attachment_dir)
        except Exception as e:
            print("Failed to access or create the target directory:")
            raise e
    
    def _feedback_backup(self, feedbacks) -> None: #QB added this
        """Save scraped json of feedback data into pickle file and set "continue_feedback_scrape_after_error
        in config file to true.
        
        feedbacks = list[dict]
        """
        with open('./tmp/feedback_backup.pkl', 'wb') as f:
            pickle.dump(feedbacks, f)
        
    def _change_config(self, key :str, value : bool): #QB added this
        """Changes values in config file."""
        
        if key == "continue_feedback_scrape_after_error":
            self.continue_feedback_scrape = value
        config = json.load(open('./tmp/config.json'))
        config[key] = value
        json.dump(config, open('./tmp/config.json', 'w'))

    def _sleep(self) -> None:
        """Depending on the time of the last request to 'Have your Say', sleep for the
        necessary time to match sleep_time.
        """
        # If less than sleep_time seconds since completion of last request, sleep
        if time.time() - self.last_request <= self.sleep_time:
            time.sleep(self.sleep_time - (time.time() - self.last_request))

    def _snake_case(self, line: str) -> str:
        """Snake case the input line.

        Parameters
        ----------
        line : str
            String to snake case.

        Returns
        -------
        str
            Snake cased input string.
        """
        line = line.replace(" ", "_")
        return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", line).lower()

    def _update_print_line(self, line: str, end: bool = False) -> None:
        """Update the line currently printed to the console with a new one.

        Parameters
        ----------
        line : str
            Line to overwrite the current output with.
        end : bool, optional
            Whether to end writing to this line, by default False. True adds a newline
            to the input string, i.e. moves the cursor into the next line.
        """
        print("\r" * self.max_print, end="")
        print(line.ljust(self.max_print), end="" if not end else "\n")
        sys.stdout.flush()  # Make sure new line is actually printed in console
        self.max_print = max(len(line), self.max_print)
