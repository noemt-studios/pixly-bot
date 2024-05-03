def get_progress_bar(progress, panes=10):
    if progress >= 1:
        return "<:green_glass_pane:1061680096685084742>" * panes
    
    progress_string = ""
    for i in range(1, panes+1):
        progress_string += "<:green_glass_pane:1061680096685084742>" if progress > i / (panes+1) else "<:grey_glass_pane:1061680098337628160>"
    
    return progress_string
