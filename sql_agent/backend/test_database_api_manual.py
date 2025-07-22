"""
Manual test script for database API and service.
This script can be run directly to test the functionality without using pytest.
"""

import asyncio
from datettetime
from typi Optional
from fastapi import HTTPExcepus

# Copy of the DatabaseService class for testing
class DatabaseService:
    """
ormation.
    """
    
    @staticmethod
    ]]:
        """
        Get list of databases accessible by  user.
        
        Args:
            user_i
            
     Returns:
            List of databasies
        """
        
        # accessible databases based on permissions
        
        # For now, return sample data
        return [
            {
    ,
                "name": "Sampl",
                "type": "mssql",
        ",
                "port": 1433,
                "default_schema": "dbo",
                "created_at": datetime.now().isoformat(),
                "updated_at": datet,
            },
            {
                "id": "db2",
                "name": "Sample SAP HANA DB",
                "type": "hana",
                "host": "localhost",
    5,
                "default_schemTEM",
                "created_at": datetime.now().),
        
            }
        ]
    
    @staticmethod
    async def connect_database(db_id: str, user_id: str) -> D
    
        Connect to a database.
    
        Args:
            db_id: Database ID          ))ervice(e_sabasest_datn(t asyncio.ru   __":
in == "__ma_name__")

if _mpleted! cotstesl Al"\n(print
      ")
  )}str(eabase: {atng from dectinn disco"Errorprint(f    e:
      ast Exception
    exceptus']}"){disc['staStatus: "t(f       prin
 n_id']}")connectio {disc['ase:om databcted frnne"Disco print(f)
       _user_id"3", "testst_12n_tebase("conatannect_dvice.discoatabaseSer await D   disc =    
 try:...")
    database disconnect_ingt("\nTestse
    prinect_databaest disconn# T    
    }")
tr(e){se schema: abas getting datorErrnt(f"   pri
     s e: Exception a
    exceptolumns)") c'columns'])}n(t[ ({le'name']} {t["      -int(f          prs']:
      ['table t in s for        ])}")
   s['tables's: {len(f"    Tableprint(           ']}")
 me'nas[ - Schema: {f"       print(     
 chemas']:n schema['sor s i
        f'])}")schemasma['hemas: {len(scer of schent(f"Numbri        pb_id']}")
chema['d{stabase:  for da"Got schema(f  print  
    )_user_id""test", 1"dbbase_schema(atavice.get_d DatabaseSer= await   schema  try:
     ...")
   emaatabase_schsting get_d\nTeprint("
    hemadatabase_sc get_
    # Test
    )}"): {str(eected error"Unexpnt(fpri        n as e:
t Exceptio
    excep_code})")statusde: {e. costatusil} (.detar: {eed erroct"Expe   print(fs e:
     n aHTTPExceptio
    except _id']}")e: {conn['dbd to databasnnectent(f"Co     prid")
   ser_it_u", "tesalid_db"invabase(_datnect.conrviceseSewait Databa= a      conn :
  ")
    tryDB ID...alid ith invtabase wdaect_ connTesting("\nntpri   
 IDlid DB invaith base wata connect_d
    # Teste)}")
    tr(: {ssedatabato ting onnec"Error cprint(f
         as e:t Exceptionexcep]}")
    tion_id'onn['connecction ID: {c"Conneint(f       pr")
 db_id']}: {conn[' to databaseectedConnt(f"in pr   ")
    user_id"test_e("db1", abasconnect_dataseService.atabit D= awaconn       try:
      ")
abase...onnect_dat c\nTesting    print("atabase
t_decconnTest  
    # ]})")
   ype'db['t]} ({e'db['nam- {  rint(f":
        pb in dbsr d")
    fo} databases:n(dbs){le"Found   print(f)
  d"test_user_i"atabases(e.get_user_dvicDatabaseSerawait 
    dbs = ..")abases.datt_user_esting ge("\nT  prints
  abaser_datt get_use 
    # Tes..")
   e.ServicbaseDatag Testint("
    prinons""" functicease servidatab"Test the     ""
ervice():tabase_sdanc def test_   )

asy      "
   r(e)}: {strom databasedisconnect fto "Failed detail=f         R,
       RRO_SERVER_EINTERNALs.HTTP_500_ode=status_c statu           n(
    TPExceptio HTaise         r")
   tr(e)}ase: {satabom dt frconnecdis"Failed to    print(f:
         ception as eexcept Ex
          }
          rmat(),w().isofoetime.no": datd_atdisconnecte        "d,
        n_inectioconon_id": nnecti "co        ,
       cted" "disconne"status":            n {
           returction
     ul disconneessflate a succmuFor now, si         #        
   l
     tion poo the connect from. Remove i   # 3     ion
    connectbase  the dataClose       # 2.      ser
 the uongs to belonecti connthe Check if   # 1.         would:
  n, thisntatiolemeeal imp In a r           #     try:
  """
   ils
       on fannecticotion: If dis  HTTPExcep    
      es:      Rais      
  on
      matistatus inforconnection         Disns:
        Retur      
       r ID
   er_id: Use          usD
  nection I Conection_id: conn           Args:
    
      
       database.rom asconnect f    Di"""
           :
 y] Anstr,) -> Dict[ strr_id:d: str, useonnection_iase(cct_databconnenc def disasyhod
     @staticmet
    
   )          "
  {str(e)}a: se schemget databa"Failed to etail=f     d   ,
        ERVER_ERROR_INTERNAL_S00HTTP_5tatus.atus_code=s  st        
      xception(aise HTTPE   r         str(e)}")
d}: {ase {db_ir databa fochem to get s"Failed print(f
           n as e:pt Exceptio       exce    raise
       :
  ionxceptPExcept HTT     e
   hemascn     retur     
                     }
   
   format()().isoime.nowed": datet"last_updat               ],
           }
                 ]
                                     }
                    ers"
    ord"Customer n": escriptio     "d                        ],
                                 }
                                 "]
     dmer_ito"cus: [ns"olumrence_c  "refe                               ,
       s"customer_table": "ence"refer                                        id"],
"customer_: [umns"      "col                                {
                                      keys": [
foreign_   "                            
 rder_id"],: ["oimary_key"      "pr                        ],
                                 e},
 ble": Fals"nulla,2)", "decimal(10"type": ount", l_amme": "tota{"na                            
        ,False}e": "nullabl", me "datetipe":"tyder_date", name": "or         {"                  
         se},e": Fal"nullabl"int", ": type_id", "stomerame": "cu {"n                            
       lse},le": Fallab"nu "int", ":, "type"order_id" {"name":                            
        s": ["column                        ",
        ": "ordersme"na                                {
                           
        },                     ormation"
mer inf": "Custoiption "descr                      
         ],eys": [reign_k        "fo                        r_id"],
tomeey": ["cusry_krima        "p                        ],
                                ": True},
 "nullable",ar(100)che": "varypil", "tame": "ema   {"n                              },
   Falsele": , "nullabchar(100)""var":  "type"name", {"name":                                alse},
    : F""nullable, ": "int"", "typeer_id "customame":        {"n                       
     ns": [ "colum                        
       ustomers","c"name":                            {
                               
  bles": [   "ta                   ,
  : "sales"name"   "                      {
                 s": [
  "schema        d,
         db_ib_id":    "d           = {
     schema 
        hemaple scte a sam Crea       # 
                       )
        
 "d} not found{db_iD e with I"Databasetail=f          d       ND,
   4_NOT_FOU40atus.HTTP_s_code=st   statu              (
   Exceptionraise HTTP            ]:
    2"db1", "dbnot in ["db_id   if       data
    hema sample scow, return   # For n     
              
   ormationchema inffor sse ataba Query the d 3.       #e
      a new onestablishon or g connecti existinGet an   # 2.          abase
 datisaccess thon to as permissie user hck if th1. Che     # 
       d:ouln, this wtiolementa imp real # In a
             try:"
      ""   ails
     trieval fschema reception: If HTTPEx          Raises:
              
on
        formatima inabase sche     Dat  
       Returns:
                  er ID
ser_id: Us  u         
 Database IDid:          db_  Args:
       
      
    ion.a informatase schematab    Get d"
     ""
       str, Any]:tr) -> Dict[d: sr_i use str,_id:(dbhemase_scaba get_datdefync 
    asthodaticmest
    @   
   )      "
    str(e)}se: {to databao connect f"Failed t  detail=            RROR,
  ER_ESERV00_INTERNAL_tatus.HTTP_5e=sus_cod  stat              ption(
xce raise HTTPE       )}")
    (eid}: {strabase {db_ct to dat conneed toil print(f"Fa        
   n as e:eptio Exc     exceptise
        raon:
       eptiept HTTPExc    exc   }
      ,
       mat()orisofe.now().t": datetim"connected_a      
          tamp()}",mes.now().tietime_{dat_id}_{db_id}"conn_{usertion_id": f"connec          _id,
      db"db_id":                
 ",nected": "con"status                return {
   
              
                 )   nd"
    not fou_id}dbe with ID {=f"Databas  detail          
        OUND,TP_404_NOT_Fstatus.HTde=tatus_co         s         (
  ionTTPExcept    raise H           ]:
 "db2", b1"["d not in db_idf    i        nection
 essful consucclate a mu, sior now      # F 
      
           ection poolconna on in  connectie theStor # 4.           atabase
 n to the da connectiosh  3. Establi  #         
 tionion informannectdatabase co. Get the  2      #e
      databasis  access th toissionpermser has if the u# 1. Check       uld:
      is wotation, thmplemenIn a real i     # 
              try:"""
 s
        on failconnectidatabase eption: If    HTTPExc
            Raises:    
     on
        s informatistatuion nnect Co       
       Returns:    
             d: User ID
user_i
  