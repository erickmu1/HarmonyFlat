import os

from music21 import converter

PROJ_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


if __name__ == '__main__':
    MIDI_DIR = PROJ_DIR + '/midi_samples'
    
    midi_stream = converter.parse(MIDI_DIR + '/Seishun_Seminar_-_Bokutachi_wa_Benkyou_ga_Dekinai_OP.mid')
    midi_stream.show('text')
