import asyncio
import math
import time
import unicodedata
import unicodedata
import datetime
import re
import traceback
# KANGED FROM UNIBORG #

async def progress(current, total, event, start, type_of_ps , speed_raw=None):
    """Generic progress_callback for both
    upload.py and download.py"""
    now = time.time()
    diff = now - start
    try:
        if round(diff % 10.00) == 0 or current == total:
            percentage = current * 100 / total
            speed = current / diff
            elapsed_time = round(diff) * 1000
            time_to_completion = round((total - current) / speed) * 1000
            estimated_total_time = elapsed_time + time_to_completion
            progress_str = "[{0}{1}]\n<b>Percent:</b> {2}%\n".format(
                ''.join(["▰" for i in range(math.floor(percentage / 5))]),
                ''.join(["▱" for i in range(20 - math.floor(percentage / 5))]),
                round(percentage, 2))

            tmp = progress_str + \
                "<b>{0}</b> of <b>{1}</b>\n<b>ETA:</b> {2}\n{3}\n\n{4}".format(
                    humanbytes(current),
                    humanbytes(total),
                    time_formatter(estimated_total_time),
                    '<b>Speed:</b> '+sizeof_fmt(speed_raw if speed_raw else speed) + '/s',
                    f'<b>💾Tamaño:</b>{humanbytes(total)}'
                )
            try:
                await event.edit("{}\n {}".format(
                    type_of_ps,
                    tmp
                ))
            except:
                pass    
    except:
        print(traceback.format_exc())
            
async def progress_mega(current, total, event, start, type_of_ps , speed_raw=None):
    """Generic progress_callback for both
    upload.py and download.py"""
    now = time.time()
    diff = now - start
    try:
        if round(diff % 1.00) == 0 or current == total:
            percentage = current * 100 / total
            speed = current / diff
            elapsed_time = round(diff) * 1000
            time_to_completion = round((total - current) / speed) * 1000
            estimated_total_time = elapsed_time + time_to_completion
            progress_str = "[{0}{1}]\n<b>Percent:</b> {2}%\n".format(
                ''.join(["▰" for i in range(math.floor(percentage / 5))]),
                ''.join(["▱" for i in range(20 - math.floor(percentage / 5))]),
                round(percentage, 2))

            tmp = progress_str + \
                "<b>{0}</b> of <b>{1}</b>\n<b>ETA:</b> {2}\n{3}\n\n{4}".format(
                    humanbytes(current),
                    humanbytes(total),
                    time_formatter(estimated_total_time),
                    '<b>Speed:</b> '+sizeof_fmt(speed_raw if speed_raw else speed) + '/s',
                    f'<b>💾Tamaño:</b>{humanbytes(total)}'
                )
            try:
                await asyncio.sleep(0)
                await event.edit("{}\n {}".format(
                    type_of_ps,
                    tmp
                ))
                await asyncio.sleep(0)
            except:
                pass    
    except:
        print(traceback.format_exc())
async def progress_yutu(d,msg,start,type_of_ps):
    """Generic progress_callback for both
    upload.py and download.py"""
    now = time.time()
    current = d.get("downloaded_bytes", 0)
    total = d.get("total_bytes") or d.get("total_bytes_estimate", 0)
    diff = now - start
    try:
        if d['status'] == 'downloading':
            if round(diff % 10.00) == 0 or current == total:
                percentage = current * 100 / total
                speed = re.sub(r'\u001b|\[0;94m|\u001b\[0m|\[0;32m|\[0m|\[0;33m', "",d.get("_speed_str", "N/A"))
                estimated_total_time = re.sub(r'\u001b|\[0;94m|\u001b\[0m|\[0;32m|\[0m|\[0;33m', "",d.get("_eta_str", d.get("eta")))
                progress_str = "[{0}{1}]\n<b>Percent:</b> {2}%\n".format(
                    ''.join(["▰" for i in range(math.floor(percentage / 5))]),
                    ''.join(["▱" for i in range(20 - math.floor(percentage / 5))]),
                    round(percentage, 2))
                tmp = progress_str + \
                    "<b>{0}</b> of <b>{1}</b>\n<b>Speed:</b>{2}\n<b>ETA:</b> {3}\n\n{4}".format(
                        humanbytes(current),
                        humanbytes(total),
                        speed,
                        estimated_total_time,
                        f'<b>💾Tamaño:</b>{humanbytes(total)}'
                    )
                if not round(percentage, 2) == 100 or round(percentage, 2) == 100.0:
                    await msg.edit("{}\n {}".format(
                        type_of_ps,
                        tmp
                    ))
                else:    
                    await msg.edit("{}\n {}".format(
                        type_of_ps,
                        'Merging...'
                    ))
        else:
            return        
    except Exception as e:
        print(traceback.format_exc())
def sizeof_fmt(num, suffix='B'):
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "%3.1f %s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f %s%s" % (num, 'Yi', suffix)

def text_progres(index,max):
	try:
		if max<1:
			max += 1
		porcent = index / max
		porcent *= 100
		porcent = round(porcent)
		make_text = ''
		index_make = 1
		make_text += '\n['
		while(index_make<21):
			if porcent >= index_make * 5: make_text+='●'
			else: make_text+='○'
			index_make+=1
		make_text += ']\n'
		return make_text
	except Exception as ex:
			return ''

def porcent(index,max):
    porcent = index / max
    porcent *= 100
    porcent = round(porcent)
    return porcent


def convert_from_bytes(size):
    power = 2**10
    n = 0
    units = {
        0: "",
        1: "kilobytes",
        2: "megabytes",
        3: "gigabytes",
        4: "terabytes"
    }
    while size > power:
        size /= power
        n += 1
    return f"{round(size, 2)} {units[n]}"

def humanbytes(size):
    """Input size in bytes,
    outputs in a human readable format"""
    # https://stackoverflow.com/a/49361727/4723940
    if not size:
        return ""
    # 2 ** 10 = 1024
    power = 2 ** 10
    raised_to_pow = 0
    dict_power_n = {
        0: "",
        1: "Ki",
        2: "Mi",
        3: "Gi",
        4: "Ti"
    }
    while size > power:
        size /= power
        raised_to_pow += 1
    return str(round(size, 2)) + " " + dict_power_n[raised_to_pow] + "B"

def time_formatter(milliseconds: int) -> str:
    """Inputs time in milliseconds, to get beautified time,
    as string"""
    seconds, milliseconds = divmod(int(milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = ((str(days) + "d, ") if days else "") + \
        ((str(hours) + "h, ") if hours else "") + \
        ((str(minutes) + "m, ") if minutes else "") + \
        ((str(seconds) + "s, ") if seconds else "") + \
        ((str(milliseconds) + "ms, ") if milliseconds else "")
    return tmp[:-2]


def createUploading(filename,totalBits,currentBits,speed,time,originalname=''):

    msg = '⏫ Subiendo A La Nube☁...\n\n'
    msg += '➤ Nombre: '+filename+'\n'
    if originalname!='':
        msg = str(msg).replace(filename,originalname)
        msg+= '➤ Parte: ' + str(filename)+'\n'
    percentage = currentBits * 100 / totalBits
    progress_str= "[{0}{1}]\nPercent: {2}%\n".format(
            ''.join(["▰" for i in range(math.floor(percentage / 5))]),
            ''.join(["▱" for i in range(20 - math.floor(percentage / 5))]),
            round(percentage, 2))
    msg += '➤ Total: '+sizeof_fmt(totalBits)+'\n\n'
    msg += '➤ Subido: '+sizeof_fmt(currentBits)+'\n\n'
    msg += '➤ Velocidad: '+sizeof_fmt(speed)+'/s\n\n'
    msg += '➤ Tiempo de Descarga: '+str(datetime.timedelta(seconds=int(time)))+'s\n\n'
    tmp = progress_str + \
            "{0} of {1}\nETA: {2}\n\n{3}\n\n{4}".format(
                humanbytes(currentBits),
                humanbytes(totalBits),
                time_formatter(time),
                'Velocidad:'+sizeof_fmt(speed)+'/s',
                f'<b>💾Tamaño:</b>{humanbytes(totalBits)}'
            )

    return tmp

def slugify(value, allow_unicode=False):
    """
    Taken from https://github.com/django/django/blob/master/django/utils/text.py
    Convert to ASCII if 'allow_unicode' is False. Convert spaces or repeated
    dashes to single dashes. Remove characters that aren't alphanumerics,
    underscores, or hyphens. Convert to lowercase. Also strip leading and
    trailing whitespace, dashes, and underscores.
    """
    value = str(value)
    ext = str(value).split('.')[-1]
    value = str(value).split('.')[0]
    if allow_unicode:
        value = unicodedata.normalize('NFKC', value)
    else:
        value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s-]', '', value.lower())
    return re.sub(r'[-\s]+', '-', value).strip('-_') + '.' + ext


