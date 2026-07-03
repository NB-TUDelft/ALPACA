from command import LCD_PUTSTR
from bus import link
from events.toolkit.custom import set_text

link.register(LCD_PUTSTR)(set_text)