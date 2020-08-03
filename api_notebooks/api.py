#imports
import pandas as pd
import numpy as np
import time
import requests
import bs4
import json
from flatten_json import flatten

class api:
    # self.apikey
    # self.region
    # tier
    # self.game_list
    # self.sum_ids
    # self.acc_ids
    # self.gam_ids
    # self.game_list
    # self.matchlist
    # self.df

    
    def __init__(self,apikey,region):
        # 20 requests every 1 seconds(s)
        # 100 requests every 2 minutes(s)
        # apikey refreshes every 24 hours
        # region = na1, euw1, kr
        # tier = CHALLENGER, GRANDMASTER, MASTER
        # game_list = list of game ids
            
        self.apikey = apikey
        self.region = region
        self.game_list = set()
        
       
    # retrieve summoner ids from tier of region in league-exp api
    def retrieve_sum_ids(self, tier):        
        sum_req = requests.get("https://{}.api.riotgames.com/lol/league-exp/v4/entries/RANKED_SOLO_5x5/{}/I?page=1&api_key={}"
                               .format(self.region,tier,self.apikey),time.sleep(1.2))
        
        assert sum_req.status_code == 200
        
        self.sum_ids = [summoner['summonerId'] for summoner in sum_req.json()]
       
    
    # translate summoner ids into account ids
    def retrieve_acc_ids(self):           
        acc_ids = []
        
        for sumid in self.sum_ids:
            acc_req = requests.get("https://{}.api.riotgames.com/lol/summoner/v4/summoners/{}?api_key={}"
                                   .format(self.region,sumid,self.apikey),time.sleep(1.2))
            
            assert acc_req.status_code == 200
            
            acc_ids.append(acc_req.json()['accountId'])
        
        self.acc_ids = acc_ids
        
        
    # retrieve matches from match history using account ids    
    def retrieve_gam_ids(self):            
        gam_ids = []

        for acc in self.acc_ids:
            mat_req = requests.get("https://{}.api.riotgames.com/lol/match/v4/matchlists/by-account/{}?api_key={}"
                                   .format(self.region,acc,self.apikey),time.sleep(1.2))

            i=0 #mechanism to stop if fails 5 times in a row
            while mat_req.status_code != 200:
                mat_req = requests.get("https://{}.api.riotgames.com/lol/match/v4/matchlists/by-account/{}?api_key={}"
                                   .format(self.region,acc,self.apikey),time.sleep(1.2))
                i+=1
                if i == 5:
                    assert 1 == 0

            gam_ids += [match['gameId'] for match in mat_req.json()['matches']]
            
        self.gam_ids = list(set(gam_ids)) # remove overlapping games
        
        self.update_game_list(gam_ids)
    

    # master game id list    
    def update_game_list(self,gam_ids):
        self.game_list = self.game_list | set(gam_ids)
        
        
    # write text file of list of game ids
    def export_game_list(self):
        with open('{}_gam_id_list.txt'.format(self.region), 'w') as f:
            for item in self.game_list:
                f.write("%s\n" % item)
                
                
    # get individual match information from gamids list via match-api
    def retrieve_game_info(self,start=0,stop=None):
        matchlist = []
        
        if stop is None:
            stop = len(self.gam_ids)

        for gam in self.gam_ids[start:stop]:
            gamreq = requests.get("https://{}.api.riotgames.com/lol/match/v4/matches/{}?api_key={}"
                                  .format(self.region,gam,self.apikey),time.sleep(1.3))

            i=0 #mechanism to stop if fails 5 times in a row
            while gamreq.status_code != 200:
                gamreq = requests.get("https://{}.api.riotgames.com/lol/match/v4/matches/{}?api_key={}"
                                      .format(self.region,gam,self.apikey),time.sleep(1.3))
                i+=1
                if i == 5:
                    assert 1 == 0

            match = flatten(gamreq.json())
            matchlist.append(match)
        
        self.matchlist = matchlist
        
    
    # create dataframe from list of match info
    def dataframe(self):
        self.df = pd.DataFrame(self.matchlist)
        
    # export df as zipped csv    
    def export_df(self):
        zip_name = '{}{}.zip'.format(region,tier)
        compress = dict(method='zip',archive_name='{}{}.csv'.format(region,tier))
        df.to_csv(zip_name,index=False,compression=compress)