#!/usr/bin/env python3
"""Prepare private Verilator sources for two complete JTBUBL instances."""

from __future__ import annotations

import argparse
from pathlib import Path


DUAL_VIDEO_DUMP = r'''void JTSim::video_dump() {
#ifdef _JTFRAME_SIM_SKIP_FRAME_DUMP
    return;
#endif
    static int LHBLl, LVBLl;
    static int cntw[2], cnth[2];
    static bool active_video;
    static int last_pxlcen=0;

    if( game.pxl_cen_b != game.pxl_cen || game.LHBL_b != game.LHBL ||
        game.LVBL_b != game.LVBL || game.HS_b != game.HS || game.VS_b != game.VS ) {
        fprintf(stderr, "\nDual-instance timing mismatch at frame %d\n", frame_cnt);
        throw runtime_error("dual JTBUBL video timing mismatch");
    }
    if( game.sample_b != game.sample ||
        (game.sample && (game.snd_left_b != game.snd_left || game.snd_right_b != game.snd_right)) ) {
        fprintf(stderr, "\nDual-instance audio mismatch at frame %d\n", frame_cnt);
        throw runtime_error("dual JTBUBL audio mismatch");
    }

    if( game.pxl_cen && !last_pxlcen ) {
        if( game.LHBL && game.LVBL ) {
            active_video = true;
            if( game.red_b != game.red || game.green_b != game.green || game.blue_b != game.blue ) {
                fprintf(stderr, "\nDual-instance pixel mismatch at frame %d\n", frame_cnt);
                throw runtime_error("dual JTBUBL active-video mismatch");
            }
        }
        if( game.LHBL && game.LVBL && frame_cnt>0 ) {
            const int MASK = (1<<_JTFRAME_COLORW)-1;
            int red   = game.red   & MASK;
            int green = game.green & MASK;
            int blue  = game.blue  & MASK;
            int red_b   = game.red_b   & MASK;
            int green_b = game.green_b & MASK;
            int blue_b  = game.blue_b  & MASK;
            int mix = 0xFF000000 |
                ( color8(blue ) << 16 ) |
                ( color8(green) <<  8 ) |
                ( color8(red  )       );
            int mix_b = 0xFF000000 |
                ( color8(blue_b ) << 16 ) |
                ( color8(green_b) <<  8 ) |
                ( color8(red_b  )       );
            dump.push( mix );
            dump_b.push( mix_b );
        }
        if( !game.LHBL && LHBLl!=0 ) {
            totalw = cntw[0];
            activew= cntw[1];
            cntw[0]=0; cntw[1]=0;
            cnth[0]++;
            if( active_video ) cnth[1]++;
            active_video = false;
            if( !game.LVBL && LVBLl!=0 ) {
                report_flip_changes();
                totalh = cnth[0];
                activeh= cnth[1];
                cnth[0]=0; cnth[1]=0;
                dump.reset();
                dump_b.reset();
                if( !game.rst && !game.ioctl_rom && !game.dwnld_busy ) {
                    int len = (activew*activeh)<<2;
                    uint32_t crc_a = storeCRC("frames/a.crc", dump.prev_buffer(), len);
                    uint32_t crc_b = storeCRC("frames/b.crc", dump_b.prev_buffer(), len);
                    if( crc_a != crc_b ) {
                        fprintf(stderr, "\nDual-instance CRC mismatch at frame %d: A=%08x B=%08x\n",
                            frame_cnt, crc_a, crc_b);
                        throw runtime_error("dual JTBUBL frame CRC mismatch");
                    }
                }
            }
            LVBLl = game.LVBL;
        } else {
            cntw[0]++;
            if( game.LHBL!=0 ) cntw[1]++;
        }
        LHBLl = game.LHBL;
    }
    last_pxlcen = game.pxl_cen;
}
'''


def prepare_test_cpp(source: Path, output: Path) -> None:
    text = source.read_text()
    old_crc = '''void storeCRC( char *data, int len ) {
    uint32_t crc32 = calcCRC32(data,len);
    ofstream of("frames/frames.crc",std::ios::app);
    if( of.is_open() ) {
        of << hex << crc32 << endl;
    }
}'''
    new_crc = '''uint32_t storeCRC( const char *filename, char *data, int len ) {
    uint32_t crc32 = calcCRC32(data,len);
    ofstream of(filename,std::ios::app);
    if( !of.is_open() ) throw runtime_error(string("cannot write ") + filename);
    of << hex << crc32 << endl;
    return crc32;
}'''
    if text.count(old_crc) != 1:
        raise SystemExit("unsupported JTFRAME test.cpp: CRC helper did not match")
    text = text.replace(old_crc, new_crc)
    old_reset_delay = "reset( simtime < RST_DLY*1000'000L ? 1 : 0);"
    new_reset_delay = "reset( simtime < _RST_DLY*1000'000L ? 1 : 0);"
    if text.count(old_reset_delay) != 1:
        raise SystemExit("unsupported JTFRAME test.cpp: reset-delay expression did not match")
    text = text.replace(old_reset_delay, new_reset_delay)
    if text.count("    } dump;") != 1:
        raise SystemExit("unsupported JTFRAME test.cpp: video buffers did not match")
    text = text.replace("    } dump;", "    } dump, dump_b;")
    start = text.find("void JTSim::video_dump() {")
    end = text.find("\nvoid JTSim::update_wav()", start)
    if start < 0 or end < 0:
        raise SystemExit("unsupported JTFRAME test.cpp: video_dump did not match")
    text = text[:start] + DUAL_VIDEO_DUMP + text[end:]
    output.write_text(text)


def prepare_game_test(source: Path, output: Path) -> None:
    text = source.read_text()
    marker = "module game_test("
    if text.count(marker) != 1:
        raise SystemExit("unsupported JTFRAME game_test.v: top module did not match")
    output.write_text(text.replace(marker, "module game_test_single(", 1))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--jtframe", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    prepare_test_cpp(args.jtframe / "verilator/test.cpp", args.out / "test.cpp")
    prepare_game_test(args.jtframe / "hdl/ver/game_test.v", args.out / "game_test_single.v")


if __name__ == "__main__":
    main()
