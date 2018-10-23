import xml.etree.ElementTree as ET
import sys
import os
import argparse

parser = argparse.ArgumentParser("GenVideoTraces")
parser.add_argument("--dash-root",
        type=str,
        required=True,
        help="The root of the DASH video tree, should contain Manifest.mpd")
parser.add_argument("--index-tmpl",
        type=str,
        default="index.html.tmpl",
        help="Location of the index.html template")
args = parser.parse_args()

TRACE_OUT = os.path.join(args.dash_root, "trace.dat")
INDEX_OUT = os.path.join(args.dash_root, "index.html")

def params_from_manifest(manifest_file):
    tree = ET.parse(os.path.join(args.dash_root, 'Manifest.mpd'))
    root_tag = tree.getroot().tag
    end_brace_loc = root_tag.find('}')
    ns = ""
    if end_brace_loc > 0:
        ns = root_tag[:end_brace_loc+1]
    
    reps = tree.getroot().find(ns + 'Period').find(ns + 'AdaptationSet')
    seg_tmpl = reps.find(ns + 'SegmentTemplate')
    dur = int(seg_tmpl.get('duration'))/int(seg_tmpl.get('timescale'))
    bws = []
    for rep in reps.findall(ns + 'Representation'):
        b = rep.get('bandwidth')
        bws.append(int(b))
    bws.sort()
    return {'bws': bws, 'url': seg_tmpl.get('media'), 'chunk_duration': dur}

# Returns an array of arrays: the ith row is the sorted list of the sizes of the
# ith chunk.
# Chunks are reported in Bytes.
def get_chunk_sizes(dash_root, bws, tmpl):
    chunks_for_rep = []
    min_size = 1e6
    all_chunk_sizes = []
    for b in bws:
        i = 1
        chunk_sizes = []
        while True:
            fname = tmpl.replace('$Bandwidth$', str(b)).replace('$Number$',
                    str(i))
            fname = os.path.join(dash_root, fname)
            if os.path.exists(fname):
                chunk_sizes.append(os.path.getsize(fname))
                i += 1
            else:
                break
        all_chunk_sizes.append(chunk_sizes)    
    return all_chunk_sizes

def write_trace(xml_dict):
    with open(TRACE_OUT, 'w') as w:
        w.write('size %d\n' % (1000 * xml_dict['chunk_duration']))
        w.write('bitrates %s\n' % ' '.join([str(b / 1024) for b in xml_dict['bws']]))
        cs = get_chunk_sizes(args.dash_root, xml_dict['bws'], xml_dict['url'])
        min_len = min([len(c) for c in cs])
        for i in range(min_len):
            w.write(' '.join([str(c[i]) for c in cs]) + '\n')

def write_tmpl(xml_dict):
    name = args.dash_root.rstrip('/').split('/')[-1]
    # Round up to the nearest Mbps
    max_y1 = 1 + max(xml_dict['bws']) / 1000 / 1000
    params = {
            "$NAME$": name,
            "$MAX_Y1$": str(max_y1),
            }
    fr = open(args.index_tmpl)
    tmpl_str = fr.read()
    fr.close()
    for k, v in params.iteritems():
        tmpl_str = tmpl_str.replace(k, v)
    fw = open(INDEX_OUT, 'w')
    fw.write(tmpl_str)
    fw.close()

xml_dict = params_from_manifest(args.dash_root)
write_trace(xml_dict)
write_tmpl(xml_dict)

