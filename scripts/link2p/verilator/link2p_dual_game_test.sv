/* Simulation-only dual-instance wrapper for the JTBUBL determinism gate. */

`ifndef JTFRAME_BUTTONS
`define JTFRAME_BUTTONS 2
`endif

module game_test(
    input           sdram_rst,

    input           rst,
    input           clk,
    input           rst24,
    input           clk24,
    input           rst48,
    input           clk48,
    input           rst96,
    input           clk96,

    output          pxl2_cen,
    output          pxl_cen,
    output   [7:0]  red,
    output   [7:0]  green,
    output   [7:0]  blue,
    output          LHBL,
    output          LVBL,
    output          HS,
    output          VS,
    output          pxl_cen_b,
    output   [7:0]  red_b,
    output   [7:0]  green_b,
    output   [7:0]  blue_b,
    output          LHBL_b,
    output          LVBL_b,
    output          HS_b,
    output          VS_b,

    input   [ 3:0]  cab_1p,
    input   [ 3:0]  coin,
    input   [ 9:0]  joystick1,
    input   [ 9:0]  joystick2,
    input   [ 9:0]  joystick3,
    input   [ 9:0]  joystick4,

    input   [15:0]  joyana_l1,
    input   [15:0]  joyana_l2,
    input   [15:0]  joyana_l3,
    input   [15:0]  joyana_l4,
    input   [15:0]  joyana_r1,
    input   [15:0]  joyana_r2,
    input   [15:0]  joyana_r3,
    input   [15:0]  joyana_r4,

    input           ioctl_rom,
    input           ioctl_cart,
    output          dwnld_busy,

`ifdef JTFRAME_SDRAM_XL
    input   [26:0]  ioctl_addr,
`else
    input   [25:0]  ioctl_addr,
`endif
    input   [ 7:0]  ioctl_dout,
    input           ioctl_wr,
    input           ioctl_ram,
    output  [ 7:0]  ioctl_din,

    input   [31:0]  status,
    input   [31:0]  dipsw,
    input           service,
    input           tilt,
    input           dip_test,
    input           dip_pause,
`ifdef JTFRAME_OSD_FLIP
    input           dip_flip,
`else
    output          dip_flip,
`endif
    input   [ 1:0]  dip_fxlevel,

    output signed [15:0] snd_left,
    output signed [15:0] snd_right,
    output          sample,
    output signed [15:0] snd_left_b,
    output signed [15:0] snd_right_b,
    output          sample_b,

    output          sdram_init,
    inout  [15:0]   SDRAM_DQ,
    output [15:0]   SDRAM_DIN,
    output [12:0]   SDRAM_A,
    output [ 1:0]   SDRAM_DQM,
    output          SDRAM_nWE,
    output          SDRAM_nCAS,
    output          SDRAM_nRAS,
    output          SDRAM_nCS,
    output [1:0]    SDRAM_BA,
    output          SDRAM_CLK,
    output          SDRAM_CKE,

    input   [3:0]   gfx_en,
    input   [7:0]   st_addr,
    output  [7:0]   st_dout,
    input   [7:0]   debug_bus,
    output  [7:0]   debug_view
);

wire pxl2_cen_b;
wire dwnld_busy_b;
wire [7:0] ioctl_din_b;
wire sdram_init_b;
wire [15:0] SDRAM_DIN_b;
wire [12:0] SDRAM_A_b;
wire [1:0] SDRAM_DQM_b, SDRAM_BA_b;
wire SDRAM_nWE_b, SDRAM_nCAS_b, SDRAM_nRAS_b, SDRAM_nCS_b;
wire SDRAM_CLK_b, SDRAM_CKE_b;
wire [7:0] st_dout_b, debug_view_b;
`ifndef JTFRAME_OSD_FLIP
wire dip_flip_b;
`endif

// A and B receive the same ROM download, DIP values, reset, and cabinet input.
// Each instance owns its own SDRAM model and all writable game state.
game_test_single u_a (.*);

game_test_single u_b (
    .*,
    .pxl2_cen   ( pxl2_cen_b   ),
    .pxl_cen    ( pxl_cen_b    ),
    .red        ( red_b        ),
    .green      ( green_b      ),
    .blue       ( blue_b       ),
    .LHBL       ( LHBL_b       ),
    .LVBL       ( LVBL_b       ),
    .HS         ( HS_b         ),
    .VS         ( VS_b         ),
    .dwnld_busy ( dwnld_busy_b ),
    .ioctl_din  ( ioctl_din_b  ),
`ifndef JTFRAME_OSD_FLIP
    .dip_flip   ( dip_flip_b   ),
`endif
    .snd_left   ( snd_left_b   ),
    .snd_right  ( snd_right_b  ),
    .sample     ( sample_b     ),
    .sdram_init ( sdram_init_b ),
    // JTBUBL uses SDRAM only for immutable ROM buses. Both independent SDRAM
    // controllers therefore read the same simulated ROM-data pins; all
    // writable game, video, palette, and MCU state remains per instance.
    .SDRAM_DQ   ( SDRAM_DQ     ),
    .SDRAM_DIN  ( SDRAM_DIN_b  ),
    .SDRAM_A    ( SDRAM_A_b    ),
    .SDRAM_DQM  ( SDRAM_DQM_b  ),
    .SDRAM_nWE  ( SDRAM_nWE_b  ),
    .SDRAM_nCAS ( SDRAM_nCAS_b ),
    .SDRAM_nRAS ( SDRAM_nRAS_b ),
    .SDRAM_nCS  ( SDRAM_nCS_b  ),
    .SDRAM_BA   ( SDRAM_BA_b   ),
    .SDRAM_CLK  ( SDRAM_CLK_b  ),
    .SDRAM_CKE  ( SDRAM_CKE_b  ),
    .st_dout    ( st_dout_b    ),
    .debug_view ( debug_view_b )
);

endmodule
