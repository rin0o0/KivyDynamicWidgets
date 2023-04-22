import os, sys
import datetime     #FOR date saving of current date
import base64       #FOR password encoding
from kivy.lang import Builder
from kivy.config import Config
Config.set('graphics', 'width', '690')   #change screen width
Config.set('graphics', 'height', '800')  #change screen height
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivy.uix.boxlayout import BoxLayout
from kivymd.uix.relativelayout import MDRelativeLayout
from kivy.core.window import Window
from kivymd.uix.button import MDRaisedButton,MDFillRoundFlatButton
from kivymd.uix.screenmanager import MDScreenManager
from kivy.metrics import dp
from kivy.properties import StringProperty,NumericProperty,ObjectProperty
from kivy.resources import resource_add_path, resource_find
from kivymd.uix.dialog import MDDialog
import sqlite3
from kivy.storage.jsonstore import JsonStore
from kivymd.uix.snackbar import BaseSnackbar

class CustomSnackbar(BaseSnackbar):
    text = StringProperty(None)
    icon = StringProperty(None)
    font_size = NumericProperty("15sp")

#Builder.load_file('./mdAppComponents.kv')    
class MainLayout(BoxLayout):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
    screen_manager = ObjectProperty(None)
    dbconn    = None
    dialogbox = None
    
    def __init__(self, *args, **kwargs):  
        super().__init__(*args, **kwargs)

        self.store = JsonStore('loggedUser.json')
        try: 
            if self.store.get('UserInfo')['firstname'] != "":
                self.screen_manager.current='dashboard_screen'
        except KeyError:
            self.screen_manager.current='login_screen'
            
    def open_icon_snackbar(self):
        snackbar = CustomSnackbar(
            text="This is a sample snackbar error!",
            icon= "close-circle",
            snackbar_x="10dp",
            snackbar_y="10dp",
            size_hint_x= (Window.width - (dp(10) * 2)) / Window.width,
            bg_color="#B71C1C"
        )
        snackbar.open()
        
    def changeTitleName(self, titlename):
        self.ids.toolbar.title = titlename

    def login_account(self):
        """
        Validate username and password from user input. If the value of login_complete
        is true, generate a Login Success dialogbox, otherwise, prompt that username and password 
        not found.
        """
        
        input_username = self.ids.log_username.text.strip()
        input_password = self.ids.log_password.pass_text.text.strip()
        login_complete = self.check_user(input_username,input_password)  
        if login_complete: 
            self.display_dialog("Login Success!")
            self.ids.screen_manager1.current = "dashboard_screen"
            self.ids.screen_manager1.transition.direction = "right" 
        else:
            self.display_dialog("Username & password not found")
           
    def register_account(self,app):
        """
        Validate registration fields using input_validate function. If the value of reg_complete
        is true, generate a Registration Success dialogbox, otherwise, prompt that an error message.
        """
        
        if self.input_validate():
            reg_complete = self.add_user()
            
            if reg_complete: 
                self.display_dialog("", True)
            else:
                self.display_dialog("Error inserting records")
           
    def add_user(self):
        self.dbconn = sqlite3.connect('kivysql.db', detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        
        dbcursor = self.dbconn.cursor()
        dbcursor.execute("INSERT INTO mstuser(username, first_name, last_name, email, password, created_at, updated_at) VALUES(:var_username, :var_firstname, :var_lastname, :var_email, :var_password, :var_created_at, :var_updated_at)", 
            {
                'var_username' : self.ids.username.text.strip(),
                'var_firstname' : self.ids.firstname.text.strip(),
                'var_lastname' : self.ids.lastname.text.strip(),
                'var_email' : self.ids.email.text.strip(),
                'var_password' : self.password_encode(self.ids.password.pass_text.text.strip()),
                'var_created_at' : datetime.datetime.now(),
                'var_updated_at' : datetime.datetime.now(),
                
            })
        if(dbcursor.rowcount<1):
            print("No record created")
            return False
        else: 
            print("Record Inserted")
            self.dbconn.commit()
            self.dbconn.close()
            return True
         
    def check_user(self, input_username,input_password):
        self.dbconn = sqlite3.connect('kivysql.db', detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        dbcursor = self.dbconn.cursor()
        dbcursor.execute("SELECT * FROM mstuser WHERE mstuser.username = :var_username AND mstuser.password = :var_password",
        {'var_username': input_username,'var_password': self.password_encode(input_password)})
        records = dbcursor.fetchall()    
        if not records: 
            print("No record created")
            return False
        else: 
            for user in records: 
                print(f"Username:{user[1]}\nFirstName:{user[2]}\nLastName:{user[3]}")
                
                self.store.put('UserInfo',code=user[0],firstname=user[2],lastname=[3],username=user[1])
            self.dbconn.commit()
            self.dbconn.close()
            return True
            
                      
    def display_dialog(self, text_msg,is_success=False):
        """
        Use to generate dialog box with parameter-based text property. If is_success is true,
        generate a customize dialog box for registration success prompt

            Parameter:
                text_msg(str)   : Message to display in dialog box
                is_success(bool): Default to False, if this is true, display a custom success
                                  dialogbox 
        """
        
        if is_success :
            self.dialogbox = None
            if not self.dialogbox:
                self.clear_registration()
                self.dialogbox = MDDialog(
                    type="custom",
                    content_cls=RegDialogContent(),
                    buttons = [MDFillRoundFlatButton(
                                    text='Return to Login',  #pad blank spaces left and right
                                    font_size="20sp",
                                    md_bg_color="orange",
                                    pos_hint={'center_x': 0.5},
                                    on_release=self.reg_success_button
                                )],
                )
            self.dialogbox.open()  
        else:
            self.dialogbox = None
            if not self.dialogbox:
                self.dialogbox = MDDialog(
                    text=f"[color=#263238]{text_msg}[/color]",
                    buttons = [MDRaisedButton(
                            text="Ok",
                            md_bg_color="orange",
                            pos_hint={'center_x': 0.5},
                            on_press=self.dismiss_dialog)],
                )
            self.dialogbox.open()  
        
    
        
    def dismiss_dialog(self,*args):
        """
        Function to close/dismiss the current dialogbox
        """
        
        if self.dialogbox: #requires to have an existing dialogbox open
            self.dialogbox.dismiss()
    
    
    
    def reg_success_button(self,*args):
        """
        A dismiss_dialog() copy, specific to registration success dialog box.
        Dismiss the dialog box and return to login screen after pressing the
        'Return to Login' button
        """
        
        if self.dialogbox: #requires to have an existing dialogbox open
            self.dismiss_dialog()
            self.screen_manager.current = "login_screen" 
            self.screen_manager.transition.direction = "right"     
        
    
           
    def input_validate(self):
        """
        Validate user input in registration screen. Returns True if all validations are passed.
        
            Returns:
                True/False(bool): 
        """
        
        #strip removes any extra spaces
        username    = self.ids.username.text.strip()  
        firstname   = self.ids.firstname.text.strip()  
        lastname    = self.ids.lastname.text.strip()  
        email       = self.ids.email.text.strip()  
        password    = self.ids.password.pass_text.text.strip()
        cbTerms     = self.ids.checkBox.active
        
        #check if any one of the fields is empty
        if not username or not firstname or not lastname or not email or not password: 
            self.display_dialog("Please fill up all required fields") 
            return False    
        #check if checkbox is not checked   
        elif not cbTerms:
            self.display_dialog("You must agree to terms and condition")
            return False
        else:
            return True   
            
    
            
    def password_encode(self,password_string):
        """
        Encode password into b64 encryption for database storage.
        
            Returns:
                password(string): encoded password in b64encoding 
        """
        
        ascii_pass  = password_string.encode("ascii")
        b64_pass    = base64.b64encode(ascii_pass)
        return b64_pass.decode("ascii")
    
    
    
    def password_decode(self,password_string):
        """
        Decode password into b64 decryption for password viewing(not in use in this app).
        
            Returns:
                password(string): decoded password
        """
        
        ascii_pass  = password_string.encode("ascii")
        b64_pass    = base64.b64decode(ascii_pass)
        return b64_pass.decode("ascii")
    
    
    
    def clear_registration(self):
        """
        Clear input fields in registration screen.
        """
        self.ids.username.text  = ''
        self.ids.firstname.text = ''
        self.ids.lastname.text  = ''
        self.ids.email.text     = ''
        self.ids.password.pass_text.text = ''
        self.ids.checkBox.active = False

        
class CustomPasswordField(MDRelativeLayout):
    text      = StringProperty()
    hint_text = StringProperty()
    pass_text = ObjectProperty(None)

class CustomPasswordRegField(MDRelativeLayout):
    text      = StringProperty()
    hint_text = StringProperty()      
    pass_text = ObjectProperty(None)

class RegDialogContent(MDBoxLayout):
    pass      

class mdAppComponentsApp(MDApp):
    def build(self):
            self.theme_cls.material_style = "M3"    
            self.theme_cls.theme_style    = "Light"
            self.theme_cls.primary_palette= "Blue"
            self.theme_cls.accent_palette = "Teal"
            return MainLayout()  
      
      
if __name__ == '__main__':
    if hasattr(sys, '_MEIPASS'):
        resource_add_path(os.path.join(sys._MEIPASS))
    mdAppComponentsApp().run()