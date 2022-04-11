# wpp-html
 
 ---
 ## How to start the operation
    Use two entries **-i** and **-o** will be our input and output
    Our input must be a txt file from whatsapp export, then our output will be our result in a html report format  

 ## Automation
    This program is referenced by a file .bat named Build-reports that automates your process in a directory containing multiple conversations exported from whatsapp.
    For edit Build-reports you can use Notepad++. The configuration is linked to especific *python* in your machine but if you want change these reference you can change in method **:exe** changing *python* for a relative path to different version of python in your machine.
    
    ```
    :exe
        for %%e in (*.txt) do echo. & echo ###################### %%e ########################## & python "%back%\%dirP%\whatsapp_convert.py" -i "%%e" -o "%cd%\%%e.html" & cd "%Input%"
        
        EXIT /b 0
    ```
