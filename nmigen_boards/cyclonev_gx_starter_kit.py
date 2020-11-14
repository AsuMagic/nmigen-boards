import os
import subprocess

from nmigen.build import *
from nmigen.vendor.intel import *
from .resources import *


__all__ = ["CycloneVGXStarterKitPlatform"]


class CycloneVGXStarterKitPlatform(IntelPlatform):
    device      = "5CGXFC5" # Cyclone V 77K LEs
    package     = "C6F27"   # FBGA-672
    speed       = "C7"
    default_clk = "clk50"
    default_rst = "rst"

    resources   = [
        # TODO: what is the difference between CLOCK_ and REFCLK_ ones? didn't implement these
        
        # TODO: the following resources and connectors are untested:
        # - all clocks except CLOCK_50_B5B
        # - ADV7513 HDMI
        # - SD card interface
        # - SRAM
        # - UART
        # - SSM2603 audio CODEC
        # - 7-segment displays

        # TODO: the following pins are unimplemented:
        # - all ADC pins
        # - the si5338c variable clocks?
        # - all refclk pins
        # - all DDR2LP pins
        # - all GPIO/arduino pins
        # - all HSMC pins
        # - all I2C pins (need to fix an issue with duplicate pin assignments)
        # - all SMA pins
        # - possibly more, this was all those of a default generated .qsf

        # CLOCK_125_{p,n}
        Resource("clk125", 0, DiffPairs("U12", "V12", dir="i"),
                 Clock(125e6), Attrs(io_standard="LVDS")),

        # CLOCK_50_B5B, Si501
        Resource("clk50", 0, Pins("R20", dir="i"),
                 Clock(50e6), Attrs(io_standard="3.3-V LVTTL")),
        # CLOCK_50_B6A, Si501
        Resource("clk50", 1, Pins("N20", dir="i"),
                 Clock(50e6), Attrs(io_standard="3.3-V LVTTL")),
        # CLOCK_50_B7A, Si5338 (fixed)
        Resource("clk50", 2, Pins("H12", dir="i"),
                 Clock(50e6), Attrs(io_standard="2.5 V")),
        # CLOCK_50_B8A, Si5338 (fixed)
        Resource("clk50", 3, Pins("M10", dir="i"),
                 Clock(50e6), Attrs(io_standard="2.5 V")),
        
        # LEDG0..LEDG7, LEDR0..LEDR9
        *LEDResources(
            pins="L7 K6 D8 E9 A5 B6 H8 H9 F7 F6 G6 G7 J8 J7 K10 K8 H7 J10",
            attrs=Attrs(io_standard="2.5 V")
        ),

        # debounced KEY0..KEY3
        *ButtonResources(
            pins="P11 P12 Y15 Y16",
            invert=True,
            attrs=Attrs(io_standard="1.2 V")
        ),

        # KEY4 / CPU_RESET_n
        Resource("rst", 0, PinsN("AB24"), Attrs(io_standard="3.3-V LVTTL")),

        # SW0..SW9
        *SwitchResources(
            pins="AC9 AE10 AD13 AC8 W11 AB10 V10 AC10 Y11 AE19",
            attrs=Attrs(io_standard="1.2 V")
        ),

        # ADV7513 HDMI
        # Note this has a lot of input formats for tx_d, but this defaults to RGB24
        # Also note that I2S0, MCLK, LRCLK, SCLK are missing compared to the DE10-Nano, which i assume is audio
        # TODO: should this be declared as a new Resource somehow to share some logic?
        Resource("adv7513", 0,
            # HDMI_TX_0..HDMI_TX_7
            Subsignal("tx_d_r", Pins("V23 AA26 W25 W26 V24 V25 U24 T23", dir="o")),
            # HDMI_TX_8..HDMI_TX_15
            Subsignal("tx_d_g", Pins("T24 T26 R23 R25 P22 P23 N25 P26", dir="o")),
            # HDMI_TX_16..HDMI_TX_23
            Subsignal("tx_d_b", Pins("P21 R24 R26 AB26 AA24 AB25 AC25 AD25", dir="o")),
            Subsignal("tx_clk", Pins("Y25", dir="o")),
            Subsignal("tx_de", Pins("Y26", dir="o")),
            Subsignal("tx_hs", Pins("U26", dir="o")),
            Subsignal("tx_vs", Pins("U25", dir="o")),
            Subsignal("tx_int", Pins("T12", dir="i"), Attrs(io_standard="1.2 V")),
            # FIXME: https://github.com/nmigen/nmigen-boards/issues/122
            Subsignal("scl", Pins("B7", dir="o"), Attrs(io_standard="2.5 V")),
            Subsignal("sda", Pins("G11", dir="io"), Attrs(io_standard="2.5 V")),
            Attrs(io_standard="3.3-V LVTTL")
        ),

        *SDCardResources(0,
            clk="AB6", cmd="W8", dat0="U7", dat1="T7", dat2="V8", dat3="T8",
            attrs=Attrs(io_standard="3.3-V LVTTL")
        ),

        # TODO: cs, oe, we, dm are defined to be active low. is this what is expected by SRAMResource?
        SRAMResource(0,
            cs="N23", oe="M22", we="G25",
            a="B25 B26 H19 H20 D25 C25 J20 J21 D22 E23 G20 F21 E21 F22 J25 J26 N24 M24",
            d="E24 E25 K24 K23 F24 G24 L23 L24 H23 H24 H22 J23 F23 G22 L22 K21",
            dm="H25 M25",
            attrs=Attrs(io_standard="3.3-V LVTTL")
        ),

        # TODO: role?
        UARTResource(0,
            rx="L9", tx="M9",
            attrs=Attrs(io_standard="2.5 V")
        ),

        # SSM2603 audio CODEC
        # TODO: is it a complete pinout? because if other boards use the same we may hit the adv7513 issue
        Resource("ssm2603", 0,
            Subsignal("adclrck", Pins("C7", dir="io")),
            Subsignal("adcdat", Pins("D7", dir="i")),
            Subsignal("daclrck", Pins("G10", dir="io")),
            Subsignal("dacdat", Pins("H10", dir="o")),
            Subsignal("xck", Pins("D6", dir="o")),
            Subsignal("bclk", Pins("E6", dir="io")),
            # FIXME: see adv7513
            Subsignal("scl", Pins("B7", dir="o")),
            Subsignal("sda", Pins("G11", dir="io")),
            Attrs(io_standard="2.5 V")
        ),

        # TODO: HEX2 and HEX3 share pins with GPIO. the selection is done through DIP S1/S2
        #       how should we handle this here? just let nmigen error out when both resources are used?

        # HEX0
        Display7SegResource(0,
            a="V19", b="V18", c="V17", d="W18", e="Y20", f="Y19", g="Y18", invert=True,
            attrs=Attrs(io_standard="1.2 V")
        ),

        # HEX1
        Display7SegResource(1,
            a="AA18", b="AD26", c="AB19", d="AE26", e="AE25", f="AC19", g="AF24", invert=True,
            attrs=Attrs(io_standard="1.2 V")
        ),

        # HEX2
        Display7SegResource(2,
            a="AD7", b="AD6", c="U20", d="V22", e="V20", f="W21", g="W20", invert=True,
            attrs=Attrs(io_standard="3.3-V LVTTL")
        ),

        # HEX3
        Display7SegResource(3,
            a="Y24", b="Y23", c="AA23", d="AA22", e="AC24", f="AC23", g="AC22", invert=True,
            attrs=Attrs(io_standard="3.3-V LVTTL")
        )
    ]
    connectors = []

    def toolchain_program(self, products, name):
        quartus_pgm = os.environ.get("QUARTUS_PGM", "quartus_pgm")
        with products.extract("{}.sof".format(name)) as bitstream_filename:
            subprocess.check_call([quartus_pgm, "--haltcc", "--mode", "JTAG",
                                   "--operation", "P;" + bitstream_filename])


if __name__ == "__main__":
    from .test.blinky import Blinky
    CycloneVGXStarterKitPlatform().build(Blinky(), do_program=True)