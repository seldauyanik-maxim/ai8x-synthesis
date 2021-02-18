###################################################################################################
# Copyright (C) Maxim Integrated Products, Inc. All Rights Reserved.
#
# Maxim Integrated Products, Inc. Default Copyright Notice:
# https://www.maximintegrated.com/en/aboutus/legal/copyrights.html
###################################################################################################
"""
Toplevel C file structure generation
"""
import rv
import tornadocnn as tc
from armx4weights import convert_to_x4_q7_weights
from eprint import wprint

COPYRIGHT = \
    '/*******************************************************************************\n' \
    '* Copyright (C) Maxim Integrated Products, Inc., All rights Reserved.\n' \
    '*\n' \
    '* This software is protected by copyright laws of the United States and\n' \
    '* of foreign countries. This material may also be protected by patent laws\n' \
    '* and technology transfer regulations of the United States and of foreign\n' \
    '* countries. This software is furnished under a license agreement and/or a\n' \
    '* nondisclosure agreement and may only be used or reproduced in accordance\n' \
    '* with the terms of those agreements. Dissemination of this information to\n' \
    '* any party or parties not specified in the license agreement and/or\n' \
    '* nondisclosure agreement is expressly prohibited.\n' \
    '*\n' \
    '* The above copyright notice and this permission notice shall be included\n' \
    '* in all copies or substantial portions of the Software.\n' \
    '*\n' \
    '* THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS\n' \
    '* OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF\n' \
    '* MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.\n' \
    '* IN NO EVENT SHALL MAXIM INTEGRATED BE LIABLE FOR ANY CLAIM, DAMAGES\n' \
    '* OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,\n' \
    '* ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR\n' \
    '* OTHER DEALINGS IN THE SOFTWARE.\n' \
    '*\n' \
    '* Except as contained in this notice, the name of Maxim Integrated\n' \
    '* Products, Inc. shall not be used except as stated in the Maxim Integrated\n' \
    '* Products, Inc. Branding Policy.\n' \
    '*\n' \
    '* The mere transfer of this software does not imply any licenses\n' \
    '* of trade secrets, proprietary technology, copyrights, patents,\n' \
    '* trademarks, maskwork rights, or any other form of intellectual\n' \
    '* property whatsoever. Maxim Integrated Products, Inc. retains all\n' \
    '* ownership rights.\n' \
    '*******************************************************************************/\n\n'


def copyright_header(
        memfile,
):
    """
    Write the copyright header to .c file handle `memfile`.
    """
    memfile.write(COPYRIGHT)


def header(
        memfile,
        apb_base,
        embedded_code=False,
        cmsis_nn=False,
        compact_weights=False,
        compact_data=False,
        weight_filename='weights.h',
        sample_filename='sampledata.h',
        master=False,
        verify_kernels=False,
        riscv=False,  # Tri-state: None/False/True
        camera=False,
        embedded_arm=False,
        fail_indicator=False,
        measure_energy=False,
        timer=None,  # pylint: disable=unused-argument
        groups=None,
        lib=False,  # Tri-state: None/False/True
        oneshot=0,
):
    """
    Write include files and forward definitions to .c file handle `memfile`.
    The APB base address is passed in `apb_base`.
    """
    memfile.write('#include <stdlib.h>\n'
                  '#include <stdint.h>\n')
    if embedded_code or verify_kernels:
        memfile.write('#include <string.h>\n')
    if embedded_code:
        memfile.write('#include <stdio.h>\n')
    if not cmsis_nn:
        if embedded_code or embedded_arm:
            memfile.write('#include "mxc.h"\n')
            if lib is None or lib:
                if tc.dev.SUPPORT_GCFR:
                    memfile.write('#include "gcfr_regs.h"\n')
                else:
                    memfile.write('#include "bbfc_regs.h"\n')
            if riscv is not None and not lib:
                memfile.write('#include "fcr_regs.h"\n'
                              '#include "sema_regs.h"\n')
        else:
            if tc.dev.MODERN_SIM:
                if camera:
                    memfile.write('#include "cameraif_regs.h"\n')
                memfile.write('#include "mxc_device.h"\n'
                              '#include "mxc_delay.h"\n'
                              '#include "mxc_assert.h"\n'
                              '#include "mxc_errors.h"\n'
                              '#include "mxc_lock.h"\n'
                              '#include "mxc_pins.h"\n'
                              '#include "mxc_sys.h"\n'
                              '#include "nvic_table.h"\n')
            memfile.write('#include "global_functions.h" // For RTL Simulation\n')
    if camera:
        memfile.write('#include "pcif_defines_af2.h"\n'
                      '#define NUM_DATA_WORDS 4\n'
                      '#include "pcif.c"\n')
    if embedded_code:
        memfile.write('#include "cnn.h"\n')
    if lib is True or lib is None:
        if embedded_code or compact_weights:
            memfile.write(f'#include "{weight_filename}"\n')
    if not lib and (embedded_code or compact_data):
        memfile.write(f'#include "{sample_filename}"\n')
    memfile.write('\n')

    if not (embedded_code or embedded_arm):
        memfile.write('#define CNN_FAIL 0\n'
                      '#define CNN_OK 1\n\n')

    if not lib and embedded_arm:
        memfile.write('extern volatile void const *__FlashStart_; // Defined in linker file\n\n')

    if not lib and not cmsis_nn and (riscv is None or riscv):
        if embedded_code or tc.dev.MODERN_SIM:
            memfile.write('volatile uint32_t cnn_time; // Stopwatch\n\n')

        if embedded_code:
            function_header(memfile, prefix='', function='fail', return_type='void')

            if fail_indicator:
                memfile.write('  mxc_gpio_cfg_t gpio_out;\n')
                memfile.write('  gpio_out.port = MXC_GPIO2;\n')
                memfile.write('  gpio_out.mask = MXC_GPIO_PIN_4;\n')
                memfile.write('  gpio_out.pad = MXC_GPIO_PAD_NONE;\n')
                memfile.write('  gpio_out.func = MXC_GPIO_FUNC_OUT;\n')
                memfile.write('  MXC_GPIO_Config(&gpio_out);\n')
                memfile.write('  MXC_GPIO_OutSet(gpio_out.port, gpio_out.mask);\n\n')

            memfile.write('  printf("\\n*** FAIL ***\\n\\n");\n')
            memfile.write('  while (1);\n')
            function_footer(memfile, return_value='void')  # fail()

    if (lib is None or lib) and not cmsis_nn and (riscv is None or riscv):
        if embedded_code or tc.dev.MODERN_SIM:
            if not riscv:
                function_header(memfile, prefix='', function='CNN_ISR',
                                return_type='void')
            else:
                function_header(memfile, prefix='', function='CNN_IRQHandler',
                                return_type='void __attribute__((interrupt("machine")))')
            memfile.write('  // Acknowledge interrupt to all groups\n')
            for _, group in enumerate(groups):
                addr = tc.dev.APB_BASE + tc.ctl_addr(group, tc.dev.REG_CTL)
                if oneshot > 0 and not tc.dev.REQUIRE_ONESHOT_CLEAR:
                    memfile.write(f'  *((volatile uint32_t *) 0x{addr:08x}) &= ~(1<<12);\n')
                else:
                    memfile.write(f'  *((volatile uint32_t *) 0x{addr:08x}) &= ~((1<<12) | 1);\n')
            memfile.write('\n')
            if embedded_code and not measure_energy:
                memfile.write('  CNN_COMPLETE; // Signal that processing is complete\n')
            memfile.write('#ifdef CNN_INFERENCE_TIMER\n'
                          '  cnn_time = MXC_TMR_SW_Stop(CNN_INFERENCE_TIMER);\n'
                          '#else\n'
                          '  cnn_time = 1;\n'
                          '#endif\n')
            if riscv:
                memfile.write('\n  NVIC_ClearPendingIRQ(CNN_IRQn);\n'
                              '  NVIC_ClearPendingEVENT(CNN_IRQn);\n')
            function_footer(memfile, return_value='void')  # ISR()
        else:
            function_header(memfile, function='wait', return_type='void')
            memfile.write('  while ((*((volatile uint32_t *) '
                          f'0x{apb_base + tc.dev.C_CNN_BASE:08x}) & (1<<12)) != 1<<12) ;\n')
            function_footer(memfile, return_value='void')  # wait()

    if master is not False and (lib is None or lib):
        addr = apb_base + tc.ctl_addr(master, tc.dev.REG_CTL)

        function_header(memfile, function='continue')
        memfile.write('  cnn_time = 0;\n\n'
                      f'  *((volatile uint32_t *) 0x{addr:08x}) |= 1; '
                      f'// Re-enable group {master}\n')
        function_footer(memfile)  # continue()

        function_header(memfile, function='stop')
        memfile.write(f'  *((volatile uint32_t *) 0x{addr:08x}) &= ~1; '
                      f'// Disable group {master}\n')
        function_footer(memfile)  # stop()


def function_header(
        memfile,
        riscv_flash=False,
        function='configure',
        arguments='void',
        return_type='int',
        prefix='cnn_',
):
    """
    Write the header for the a function to `memfile`. Optionally add the RV32 Flash attribute
    when `riscv_flash`. The function name is composed from `prefix` (default: 'cnn') and
    `function_name`, the return type is `return_type` (default: 'int').
    """
    if memfile is None:
        return
    if riscv_flash:
        memfile.write(rv.RISCV_FLASH)
    memfile.write(f'{return_type} {prefix}{function}({arguments})\n{{\n')


def function_footer(
        memfile,
        return_value='CNN_OK',
):
    """
    Write the footer for a function to `memfile`, either returning `return_value` or nothing
    when `return_value` is 'void'.
    """
    if memfile is None:
        return
    if return_value != 'void':
        memfile.write(f'\n  return {return_value};\n')
    memfile.write('}\n\n')


def write_ml_data(
        memfile,
        output_width,
):
    """
    Write the ml_data variable with `output_width` to `memfile`.
    """
    if output_width != 32:
        memfile.write('static int32_t ml_data32[(CNN_NUM_OUTPUTS + '
                      f'{32 // output_width - 1}) / {32 // output_width}];\n')
    else:
        memfile.write('static int32_t ml_data[CNN_NUM_OUTPUTS];\n')


def main(
        memfile,
        apifile,
        classification_layer=False,
        unload=False,
        softmax=False,
        embedded_code=False,
        oneshot=0,
        stopstart=False,
        riscv=None,
        riscv_exclusive=False,
        riscv_flash=False,  # pylint: disable=unused-argument
        riscv_cache=False,
        riscv_debug=False,
        debugwait=1,
        camera=False,
        camera_format=None,
        device=84,
        channels=None,
        sleep=False,
        output_width=8,
        num_classes=None,  # pylint: disable=unused-argument
        clock_trim=None,
        embedded_arm=False,
        groups=None,
        boost=None,
        forever=False,
        fifo=False,
        mexpress=False,  # pylint: disable=unused-argument
        measure_energy=False,
        timer=None,  # pylint: disable=unused-argument
        pll=False,
        bias=False,
        verify_kernels=False,
        load_kernels=True,
        compact_weights=False,  # pylint: disable=unused-argument
        wfi=True,
):
    """
    Write the main function (including an optional call to the fully connected layer if
    `classification_layer` is `True`) to `memfile`.
    """
    mfile = apifile or memfile

    assert groups is not None
    mask = 0
    for _, group in enumerate(groups):
        mask |= 1 << group
    unmask = ~mask & ((1 << tc.dev.P_NUMGROUPS_ALL) - 1)

    if softmax and output_width == 8:
        wprint('--softmax should only be used with `output_width: 32`.')

    if unload and not softmax:
        write_ml_data(memfile, output_width)
        memfile.write('\n')

    if riscv is not None and not riscv and (embedded_arm or tc.dev.MODERN_SIM):
        function_header(memfile, prefix='', function='WakeISR', return_type='void')
        memfile.write('  MXC_SEMA->irq0 = MXC_F_SEMA_IRQ0_EN & ~MXC_F_SEMA_IRQ0_CM4_IRQ;\n')
        function_footer(memfile, return_value='void')  # WakeISR()

    # Add this to RTL simulations where it's missing from the SDK
    if riscv is not None and not riscv and sleep and not embedded_code:
        function_header(memfile, prefix='', function='_MXC_LP_ClearWakeStatus', return_type='void')
        memfile.write('  /* Write 1 to clear */\n'
                      '  MXC_PWRSEQ->lpwkst0 = 0xFFFFFFFF;\n'
                      '  MXC_PWRSEQ->lpwkst1 = 0xFFFFFFFF;\n'
                      '  MXC_PWRSEQ->lppwst  = 0xFFFFFFFF;\n')
        function_footer(memfile, return_value='void')  # _MXC_LP_ClearWakeStatus

    function_header(memfile, prefix='', function='main')
    if clock_trim is not None and not riscv:
        memfile.write('  uint32_t trim;\n')
    if embedded_code and (classification_layer or softmax) or oneshot > 0 or measure_energy:
        memfile.write('  int i;\n')
    if embedded_code and not forever and (classification_layer or softmax):
        memfile.write('  int digs, tens;\n')
        if output_width != 32:
            memfile.write(f'int{output_width}_t *ml_data = '
                          f'(int{output_width}_t *) ml_data32;\n')
    if embedded_code and (classification_layer or softmax) or oneshot > 0:
        memfile.write('\n')

    bbfc = 'BBFC' if not tc.dev.SUPPORT_GCFR else 'GCFR'

    if riscv is None or not riscv:
        if embedded_code or embedded_arm:
            if device == 84:
                memfile.write('  icache_enable();\n\n')
                memfile.write('  SYS_ClockEnable(SYS_PERIPH_CLOCK_AI);\n')
            else:
                memfile.write('  MXC_ICC_Enable(MXC_ICC0); // Enable cache\n\n')
                if clock_trim is not None:
                    memfile.write('  // Manual clock trim override:\n')
                    memfile.write('  *((volatile uint32_t *) 0x40000c00) = 1; '
                                  '// Set TME\n')
                    if clock_trim[0] or clock_trim[1]:
                        memfile.write('  trim = *((volatile uint32_t *) 0x40005420);\n')
                        if clock_trim[0]:
                            memfile.write('  trim &= ~0xffff;\n'
                                          f'  trim |= 0x{clock_trim[0]:x}; '
                                          '// HIRC8M (7.3728 MHz) trim\n')
                        if clock_trim[1]:
                            memfile.write('  trim &= ~(0x1ff << 22);\n'
                                          f'  trim |= 0x{clock_trim[1]:x} << 22; '
                                          '// HIRC (60 MHz) trim\n')
                        memfile.write('  *((volatile uint32_t *) 0x40005420) = trim;\n')
                    if clock_trim[2]:
                        memfile.write('  trim = *((volatile uint32_t *) 0x40005440) & '
                                      '~(0x1ff << 15);\n')
                        memfile.write('  *((volatile uint32_t *) 0x40005440) = '
                                      'trim | (0xff << 15); // HILIM\n')
                        memfile.write('  *((volatile uint32_t *) 0x40006c04) = '
                                      f'0x{clock_trim[2]:x}; // HIRC96M (100 MHz) trim\n')
                    memfile.write('  *((volatile uint32_t *) 0x40000c00) = 0; '
                                  '// Clear TME\n\n')

                memfile.write(f'  // Switch to {tc.dev.IPO_SPEED} MHz clock\n'
                              '  MXC_SYS_Clock_Select(MXC_SYS_CLOCK_IPO);\n')
                if pll:
                    memfile.write('  MXC_GCR->ito_ctrl |= MXC_F_GCR_ITO_CTRL_EN;'
                                  ' // Enable PLL (ITO)\n')
                memfile.write('  SystemCoreClockUpdate();\n')
        else:
            memfile.write('  icache_enable();\n\n')
            if device == 84:
                memfile.write('  MXC_GCR->perckcn1 &= ~0x20; // Enable CNN clock\n')
            else:
                memfile.write('  *((volatile uint32_t *) 0x40000c00) = 0x00000001; // Set TME\n')
                memfile.write('  *((volatile uint32_t *) 0x40006c04) = 0x000001a0; // 96M trim\n')
                memfile.write('  *((volatile uint32_t *) 0x40000c00) = 0x00000000; '
                              '// Clear TME\n\n')
                if tc.dev.SUPPORT_GCFR:
                    memfile.write('  MXC_GCR->clkctrl |= MXC_F_GCR_CLKCTRL_IPO_EN;'
                                  ' // Enable internal primary osc (IPO)\n')
                    if pll:
                        memfile.write('  MXC_GCR->ito_ctrl |= MXC_F_GCR_ITO_CTRL_EN;'
                                      ' // Enable PLL (ITO)\n')
                    memfile.write('  while ((MXC_GCR->clkctrl & MXC_F_GCR_CLKCTRL_IPO_RDY) == 0) ;'
                                  ' // Wait for osc\n'
                                  '  MXC_GCR->clkctrl |= MXC_S_GCR_CLKCTRL_SYSCLK_SEL_IPO;'
                                  ' // Select osc\n')

                    if not tc.dev.MODERN_SIM:
                        memfile.write('\n  // Reset all domains, restore power to CNN\n')
                        memfile.write('  MXC_GCFR->reg3 = 0xf; // Reset\n')
                        memfile.write(f'  MXC_GCFR->reg1 = 0x{mask:01x}; // Mask memory\n')
                        memfile.write(f'  MXC_GCFR->reg0 = 0x{mask:01x}; // Power\n')
                        memfile.write(f'  MXC_GCFR->reg2 = 0x{unmask:01x}; // Iso\n')
                        memfile.write('  MXC_GCFR->reg3 = 0x0; // Reset\n\n')

                        memfile.write('  MXC_GCR->pclkdiv &= ~(MXC_F_GCR_PCLKDIV_CNNCLKDIV | '
                                      'MXC_F_GCR_PCLKDIV_CNNCLKSEL);\n'
                                      '  MXC_GCR->pclkdiv |= MXC_S_GCR_PCLKDIV_CNNCLKDIV_DIV1; '
                                      '// CNN clock: APB div 1\n')
                        memfile.write('  MXC_GCR->pclkdis0 &= ~MXC_F_GCR_PCLKDIS0_CNN;'
                                      ' // Enable CNN clock\n')
                else:
                    memfile.write('  MXC_GCR->clkcn |= MXC_F_GCR_CLKCN_HIRC96M_EN;'
                                  ' // Enable 96M\n')
                    memfile.write('  while ((MXC_GCR->clkcn & MXC_F_GCR_CLKCN_HIRC96M_RDY) == 0) ;'
                                  ' // Wait for 96M\n')
                    memfile.write('  MXC_GCR->clkcn |= MXC_S_GCR_CLKCN_CLKSEL_HIRC96;'
                                  ' // Select 96M\n')

                    if not tc.dev.MODERN_SIM:
                        memfile.write('\n  // Reset all domains, restore power to CNN\n')
                        memfile.write(f'  MXC_{bbfc}->reg3 = 0xf; // Reset\n')
                        memfile.write(f'  MXC_{bbfc}->reg1 = 0x{mask:01x}; // Mask memory\n')
                        memfile.write(f'  MXC_{bbfc}->reg0 = 0x{mask:01x}; // Power\n')
                        memfile.write(f'  MXC_{bbfc}->reg2 = 0x{unmask:01x}; // Iso\n')
                        memfile.write(f'  MXC_{bbfc}->reg3 = 0x0; // Reset\n\n')

                        memfile.write('  MXC_GCR->pckdiv = 0x00010000; // CNN clock 96M div 2\n')
                        memfile.write('  MXC_GCR->perckcn &= ~0x2000000; // Enable CNN clock\n')

        if riscv is not None:
            if riscv_cache:
                if embedded_code or embedded_arm:
                    memfile.write('\n  MXC_FCR->urvbootaddr = (uint32_t) &__FlashStart_; '
                                  '// Set RISC-V boot address\n')
                elif tc.dev.MODERN_SIM:
                    memfile.write(f'  MXC_FCR->urvbootaddr = 0x{rv.RISCV_CODE_ORIGIN:08x}; '
                                  '// Set RISC-V boot address\n')
                else:
                    memfile.write(f'  MXC_NBBFC->reg4 = 0x{rv.RISCV_CODE_ORIGIN:08x}; '
                                  '// Set RISC-V boot address\n')
            elif tc.dev.MODERN_SIM:
                memfile.write(f'  MXC_FCR->urvbootaddr = 0x{tc.dev.RISCV_SRAM_ORIGIN:08x}; '
                              '// Set RISC-V boot address\n')
            if riscv_exclusive:
                if embedded_code or embedded_arm or tc.dev.MODERN_SIM:
                    memfile.write('  MXC_FCR->urvctrl |= 0x00000001; '
                                  '// Exclusive SRAM access for RISC-V\n')
                else:
                    memfile.write('  *((volatile uint32_t *) 0x40000814) |= 0x00000001; '
                                  '// Exclusive SRAM access for RISC-V (MXC_NBBFC->reg5)\n')
            if embedded_code or embedded_arm or tc.dev.MODERN_SIM:
                memfile.write('  MXC_SYS_ClockEnable(MXC_SYS_PERIPH_CLOCK_SMPHR); '
                              '// Enable Sempahore clock\n'
                              '  NVIC_SetVector(RISCV_IRQn, WakeISR); // Set wakeup ISR\n')
                if (embedded_code or embedded_arm) and debugwait:
                    memfile.write('\n  // DO NOT DELETE THIS LINE:\n'
                                  f'  MXC_Delay(SEC({debugwait})); '
                                  '// Let debugger interrupt if needed\n\n')
                memfile.write('  MXC_SYS_ClockEnable(MXC_SYS_PERIPH_CLOCK_CPU1); '
                              '// Enable RISC-V clock\n')
            else:
                memfile.write('  MXC_GCR->perckcn1 &= ~MXC_F_GCR_PERCKCN1_CPU1; '
                              '// Enable RISC-V clock\n')
        else:
            if (embedded_code or embedded_arm) and debugwait:
                memfile.write('\n  printf("Waiting...\\n");\n\n'
                              '  // DO NOT DELETE THIS LINE:\n'
                              f'  MXC_Delay(SEC({debugwait})); '
                              '// Let debugger interrupt if needed\n')
        memfile.write('\n')
    elif riscv:
        if riscv_debug and embedded_code:
            memfile.write('  Debug_Init(); // Set up RISCV JTAG\n')
        if riscv_cache:
            if not embedded_code:
                memfile.write('  icache1_enable();\n')
                memfile.write('  invalidate_icache1();\n\n')
            else:
                memfile.write('  MXC_ICC_Enable(MXC_ICC1); // Enable cache\n\n')

    if camera:
        memfile.write('  enable_pcif_clock(); // Enable camera clock\n')
        memfile.write('  set_pcif_gpio_altf();\n\n')
        if camera_format == 555:
            mode = '10'
            comment = '555'
        elif camera_format == 565:
            mode = '12'
            comment = '565'
        else:
            mode = '8'  # Default
            comment = '888'
        memfile.write(f'  // Enable {comment} format single image in external timing mode\n')
        if not tc.dev.MODERN_SIM:
            memfile.write('  MXC_CAMERAIF0->ctrl = MXC_S_CAMERAIF_CTRL_READ_MODE_SINGLE_IMG +\n'
                          f'                        MXC_S_CAMERAIF_CTRL_DATA_WIDTH_{mode}BIT +\n'
                          '                        MXC_S_CAMERAIF_CTRL_DS_TIMING_EN_DIS +\n'
                          '                        MXC_S_CAMERAIF_CTRL_PCIF_SYS_EN_EN')
            if channels == 3:
                memfile.write(' +\n                        (1<<30);\n\n')
            else:
                memfile.write(';\n\n')
        else:
            memfile.write('  MXC_PCIF->ctrl = MXC_S_CAMERAIF_CTRL_READ_MODE_SINGLE_IMG +\n'
                          f'                   MXC_S_CAMERAIF_CTRL_DATA_WIDTH_{mode}BIT +\n'
                          '                   MXC_F_CAMERAIF_CTRL_PCIF_SYS')
            if channels == 3:
                memfile.write(' +\n                   MXC_F_CAMERAIF_CTRL_THREE_CH_EN;\n\n')
            else:
                memfile.write(';\n\n')

    if riscv is None or riscv:
        if embedded_code or tc.dev.MODERN_SIM:
            if measure_energy:
                memfile.write('  cnn_disable(); // Disable clock and power to CNN\n'
                              '  // Enable primary clock\n'
                              '  MXC_SYS_ClockSourceEnable(MXC_SYS_CLOCK_IPO);\n\n'
                              '  printf("Measuring system base power...\\n");\n'
                              '  SYS_START;\n')
                if not riscv:
                    memfile.write('  MXC_Delay(SEC(1));\n')
                else:
                    memfile.write('  MXC_TMR_Delay(MXC_TMR0, 1000000);\n')
                memfile.write('  SYS_COMPLETE;\n')

            if embedded_code and apifile is not None:
                memfile.write('  // Enable peripheral, enable CNN interrupt, turn on CNN clock\n'
                              f'  // CNN clock: {tc.dev.PLL_SPEED if pll else tc.dev.APB_SPEED} '
                              'MHz div 1\n'
                              '  cnn_enable(MXC_S_GCR_PCLKDIV_CNNCLKSEL_'
                              f'{"ITO" if pll else "PCLK"}, MXC_S_GCR_PCLKDIV_CNNCLKDIV_DIV1);\n')
                function_header(apifile, function='enable',
                                arguments='uint32_t clock_source, uint32_t clock_divider')

            mfile.write('  // Reset all domains, restore power to CNN\n')
            mfile.write(f'  MXC_{bbfc}->reg3 = 0xf; // Reset\n')
            mfile.write(f'  MXC_{bbfc}->reg1 = 0x{mask:01x}; // Mask memory\n')
            mfile.write(f'  MXC_{bbfc}->reg0 = 0x{mask:01x}; // Power\n')
            mfile.write(f'  MXC_{bbfc}->reg2 = 0x{unmask:01x}; // Iso\n')
            mfile.write(f'  MXC_{bbfc}->reg3 = 0x0; // Reset\n\n')

            if embedded_code and apifile is not None:
                if tc.dev.SUPPORT_PLL:
                    mfile.write('  if (clock_source == MXC_F_GCR_PCLKDIV_CNNCLKSEL_ITO)\n  ')
                    mfile.write('  while ((MXC_GCR->ito_ctrl & MXC_F_GCR_ITO_CTRL_RDY) != '
                                'MXC_F_GCR_ITO_CTRL_RDY) ; // Wait for PLL\n')
                mfile.write('  MXC_GCR->pclkdiv = (MXC_GCR->pclkdiv & '
                            '~(MXC_F_GCR_PCLKDIV_CNNCLKDIV | MXC_F_GCR_PCLKDIV_CNNCLKSEL))\n'
                            '                     | clock_divider | clock_source;\n')
            else:
                select_clock(mfile, 'PCLK', 'DIV1', 'CNN clock: APB div 1')

            mfile.write('  MXC_SYS_ClockEnable(MXC_SYS_PERIPH_CLOCK_CNN); '
                        '// Enable CNN clock\n\n')

            if not riscv:
                mfile.write('  NVIC_SetVector(CNN_IRQn, CNN_ISR); '
                            '// Set CNN complete vector\n')
            else:
                mfile.write('  // Set CNN complete vector\n'
                            '  __enable_irq();\n'
                            '  NVIC_EnableIRQ(CNN_IRQn);\n'
                            '  NVIC_EnableEVENT(CNN_IRQn);\n')

            if embedded_code and apifile is not None:
                function_footer(apifile)  # enable()
                function_header(apifile, function='boost_enable',
                                arguments='mxc_gpio_regs_t *port, uint32_t pin')

            if boost is not None or apifile is not None:
                if boost and apifile is None:
                    memfile.write(f'\n  // Configure P{boost[0]}.{boost[1]}, '
                                  'turn on the CNN Boost\n')
                mfile.write('  mxc_gpio_cfg_t gpio_out;\n')
                if boost and apifile is None:
                    memfile.write(f'  gpio_out.port = MXC_GPIO{boost[0]};\n')
                    memfile.write(f'  gpio_out.mask = MXC_GPIO_PIN_{boost[1]};\n')
                else:
                    mfile.write('  gpio_out.port = port;\n')
                    mfile.write('  gpio_out.mask = pin;\n')
                    if boost:
                        memfile.write(f'  cnn_boost_enable(MXC_GPIO{boost[0]}, '
                                      f'MXC_GPIO_PIN_{boost[1]}); // Turn on the boost circuit\n')
                mfile.write('  gpio_out.pad = MXC_GPIO_PAD_NONE;\n')
                mfile.write('  gpio_out.func = MXC_GPIO_FUNC_OUT;\n')
                mfile.write('  MXC_GPIO_Config(&gpio_out);\n')
                mfile.write('  MXC_GPIO_OutSet(gpio_out.port, gpio_out.mask);\n')

            if embedded_code and apifile is not None:
                function_footer(apifile)  # boost_enable() or enable()

            memfile.write('\n')

        if embedded_code:
            memfile.write('  printf("\\n*** CNN Inference Test ***\\n");\n\n'
                          '  cnn_init(); // Bring state machine into consistent state\n')
            if measure_energy:
                if pll:
                    select_clock(memfile, 'ITO', 'DIV1', 'Switch CNN clock to PLL (ITO)')

                memfile.write('\n  printf("Measuring weight loading...\\n");\n'
                              '  CNN_START;\n'
                              '  for (i = 0; i < 100; i++)\n'
                              '    cnn_load_weights(); // Load kernels\n'
                              '  CNN_COMPLETE;\n\n'
                              '  printf("Measuring input loading...\\n");\n'
                              '  MXC_TMR_Delay(MXC_TMR0, 500000);\n'
                              '  CNN_START;\n'
                              '  for (i = 0; i < 100; i++)\n'
                              '    load_input(); // Load data input\n'
                              '  CNN_COMPLETE;\n\n')
            else:
                memfile.write('  cnn_load_weights(); // Load kernels\n')
            if verify_kernels:
                memfile.write('  if (cnn_verify_weights() != CNN_OK) fail();\n')
            if bias:
                memfile.write('  cnn_load_bias();\n')
            else:
                memfile.write('  // cnn_load_bias(); // Not used in this network\n')
            memfile.write('  cnn_configure(); // Configure state machine\n')
            if not measure_energy:
                if not fifo:
                    memfile.write('  load_input(); // Load data input\n')
                memfile.write('  cnn_start(); // Start CNN processing\n')
                if fifo:
                    memfile.write('  load_input(); // Load data input via FIFO\n')
            memfile.write('\n')
        else:
            memfile.write('  cnn_init(); // Bring state machine into consistent state\n')
            if load_kernels:
                memfile.write('  cnn_load_weights(); // Load kernels\n')
            else:
                memfile.write('  // Kernels are pre-loaded\n')
            if verify_kernels:
                memfile.write('  if (cnn_verify_weights() != CNN_OK) { fail(); pass(); '
                              'return 0; }\n')
            if bias:
                memfile.write('  cnn_load_bias();\n')
            else:
                memfile.write('  // No bias values\n')
            memfile.write('  if (cnn_configure() != CNN_OK) { fail(); pass(); return 0; }\n')

        if stopstart:
            memfile.write('\n  cnn_stop();\n')
            memfile.write('  cnn_continue();\n\n')

        if not measure_energy:
            if embedded_code or tc.dev.MODERN_SIM:
                if wfi:
                    memfile.write('  while (cnn_time == 0)\n')
                    if not riscv:
                        memfile.write('    __WFI(); // Wait for CNN\n\n')
                    else:
                        memfile.write('    asm volatile("wfi"); // Wait for CNN\n\n')
                else:
                    memfile.write('  while (cnn_time == 0); // Spin wait\n')
            else:
                memfile.write('  cnn_wait();\n\n')
        else:
            memfile.write('  printf("Measuring input load + inference...\\n");\n'
                          '  MXC_TMR_Delay(MXC_TMR0, 500000);\n'
                          '  CNN_START; // Allow capture of processing time\n'
                          '  for (i = 0; i < 100; i++) {\n')
            if not fifo:
                memfile.write('    load_input(); // Load data input\n')
            memfile.write('    cnn_start(); // Run inference\n')
            if fifo:
                memfile.write('    load_input(); // Load data input via FIFO\n')
            memfile.write('    while (cnn_time == 0)\n')
            if not riscv:
                memfile.write('      __WFI(); // Wait for CNN\n')
            else:
                memfile.write('      asm volatile("wfi"); // Wait for CNN\n')
            memfile.write('  }\n'
                          '  CNN_COMPLETE;\n\n')

        if oneshot > 0:
            memfile.write(f'  for (i = 0; i < {oneshot}; i++) {{\n')
            memfile.write('    cnn_continue();\n')
            if embedded_code or tc.dev.MODERN_SIM:
                memfile.write('    while (cnn_time == 0)\n')
                if not riscv:
                    memfile.write('      __WFI(); // Wait for CNN\n')
                else:
                    memfile.write('      asm volatile("wfi"); // Wait for CNN\n')
            else:
                memfile.write('    cnn_wait();\n')
            memfile.write('  }\n\n')

        if pll:
            select_clock(memfile, 'PCLK', 'DIV1', 'Switch CNN clock and disable PLL')
            memfile.write('  MXC_GCR->ito_ctrl &= ~MXC_F_GCR_ITO_CTRL_EN;\n\n')

        if embedded_code and apifile is not None:
            function_header(apifile, function='boost_disable',
                            arguments='mxc_gpio_regs_t *port, uint32_t pin')
            mfile.write('  mxc_gpio_cfg_t gpio_out;\n')
            mfile.write('  gpio_out.port = port;\n')
            mfile.write('  gpio_out.mask = pin;\n')
            mfile.write('  gpio_out.pad = MXC_GPIO_PAD_NONE;\n')
            mfile.write('  gpio_out.func = MXC_GPIO_FUNC_OUT;\n')
            mfile.write('  MXC_GPIO_Config(&gpio_out);\n')
            mfile.write('  MXC_GPIO_OutSet(gpio_out.port, gpio_out.mask);\n')
            function_footer(apifile)  # boost_disable()

        if not forever and boost is not None:
            if apifile is None:
                memfile.write('  // Turn off the CNN Boost\n')
                memfile.write('  MXC_GPIO_OutClr(gpio_out.port, gpio_out.mask);\n\n')
            else:
                memfile.write(f'  cnn_boost_disable(MXC_GPIO{boost[0]}, '
                              f'MXC_GPIO_PIN_{boost[1]}); // Turn off the boost circuit\n\n')

        memfile.write('  if (check_output() != CNN_OK) fail();\n')
        if classification_layer or softmax:
            memfile.write(f'  {"softmax" if softmax else "fc"}_layer();\n')
        elif unload:
            memfile.write('  cnn_unload((uint32_t *) '
                          f'ml_data{"32" if output_width != 32 else ""});\n')
        if classification_layer:
            memfile.write('  if (fc_verify() != CNN_OK) fail();\n')

        if embedded_code:
            memfile.write('\n  printf("\\n*** PASS ***\\n\\n");\n\n'
                          '#ifdef CNN_INFERENCE_TIMER\n'
                          f'  printf("Approximate {"data loading and " if fifo else ""}'
                          'inference time: %d us\\n\\n", cnn_time);\n'
                          '#endif\n\n')
            if measure_energy:
                memfile.write('  printf("See monitor display for inference energy.\\n\\n");\n\n')

        if not forever:
            if embedded_code and apifile is not None:
                memfile.write('  cnn_disable(); // Shut down CNN clock, disable peripheral\n\n')
                function_header(apifile, function='disable')
            if embedded_code or tc.dev.MODERN_SIM:
                mfile.write('  // Disable CNN clock\n'
                            '  MXC_SYS_ClockDisable(MXC_SYS_PERIPH_CLOCK_CNN);\n\n')
            mfile.write('  // Disable power to CNN\n')
            mfile.write(f'  MXC_{bbfc}->reg3 = 0xf; // Reset\n')
            mfile.write(f'  MXC_{bbfc}->reg1 = 0x0; // Mask memory\n')
            mfile.write(f'  MXC_{bbfc}->reg0 = 0x0; // Power\n')
            mfile.write(f'  MXC_{bbfc}->reg2 = 0xf; // Iso\n')
            mfile.write(f'  MXC_{bbfc}->reg3 = 0x0; // Reset\n')

            if embedded_code and apifile is not None:
                function_footer(apifile)  # disable()

        if not forever:
            if classification_layer or softmax:
                memfile.write('  printf("Classification results:\\n");\n'
                              '  for (i = 0; i < CNN_NUM_OUTPUTS; i++) {\n'
                              '    digs = (1000 * ml_softmax[i] + 0x4000) >> 15;\n'
                              '    tens = digs % 10;\n'
                              '    digs = digs / 10;\n'
                              '    printf("[%7d] -> Class %d: %d.%d%%\\n", '
                              f'{"fc_output" if classification_layer else "ml_data"}[i], '
                              'i, digs, tens);\n'
                              '  }\n')
        else:
            memfile.write('  printf("Starting endless loop...\\n");\n\n  LED_On(1);\n\n'
                          '  while(1) {\n'
                          '    cnn_start();\n')
            if embedded_code or tc.dev.MODERN_SIM:
                memfile.write('    while (cnn_time == 0)\n')
                if not riscv:
                    memfile.write('      __WFI(); // Wait for CNN\n')
                else:
                    memfile.write('      asm volatile("wfi"); // Wait for CNN\n')
            else:
                memfile.write('    cnn_wait();\n')

            memfile.write('  }\n')

    if riscv is not None:
        if not riscv:
            if sleep:
                if tc.dev.REQUIRE_SEMA_LPWKEN:
                    memfile.write('  MXC_PWRSEQ->lppwen |= 0x400; // CPU1WKEN=1\n')
                memfile.write(f'  {"_" if not embedded_code else ""}MXC_LP_ClearWakeStatus();\n'
                              '  SCB->SCR |= SCB_SCR_SLEEPDEEP_Msk; // SLEEPDEEP=1\n')
            memfile.write('  __WFI(); // Let RISC-V run\n')
        elif embedded_code or tc.dev.MODERN_SIM:
            memfile.write('\n  // Signal the Cortex-M4\n'
                          '  MXC_SEMA->irq0 = MXC_F_SEMA_IRQ0_EN | MXC_F_SEMA_IRQ0_CM4_IRQ;\n')

    if not embedded_code and not embedded_arm:
        memfile.write('\n  pass();')
    function_footer(memfile, return_value='0')  # Exit main - don't change from 0


def fc_layer(
        memfile,
        weights_fh,
        weights,
        bias,
        cmsis_nn=False,
        softmax_only=False,
        output_width=8,
        num_classes=None,  # pylint: disable=unused-argument
):
    """
    Write the call to the fully connected layer with the given `weights` and
    `bias` to `memfile`. The `bias` argument can be `None`.
    """
    memfile.write('// Classification layer:\n')
    if not softmax_only:
        memfile.write(f'#define FC_IN {weights.shape[1]}\n')

    if not softmax_only:
        weights = convert_to_x4_q7_weights(weights)

        c_define(weights_fh, weights, 'FC_WEIGHTS', '%d', 16)
        memfile.write('static const q7_t fc_weights[] = FC_WEIGHTS;\n\n')

    if not cmsis_nn:
        write_ml_data(memfile, output_width)
    if not softmax_only:
        memfile.write('static q15_t fc_buffer[FC_IN];\n')
        memfile.write('static q15_t fc_output[CNN_NUM_OUTPUTS];\n')
    memfile.write('static q15_t ml_softmax[CNN_NUM_OUTPUTS];\n\n')

    if bias is not None and not softmax_only:
        c_define(weights_fh, bias, 'FC_BIAS', '%d', 16)
        memfile.write('static const q7_t fc_bias[] = FC_BIAS;\n\n')

    if not cmsis_nn:
        function_header(memfile, prefix='',
                        function=f'{"softmax" if softmax_only else "fc"}_layer',
                        return_type='void')
        memfile.write(f'  cnn_unload((uint32_t *) ml_data{"32" if output_width != 32 else ""});\n')
    else:
        function_header(memfile, prefix='', function='fc_layer', arguments='q7_t *ml_data',
                        return_type='void')

    if not softmax_only:
        memfile.write('  arm_fully_connected_q7_q8p7_opt((q7_t *) ml_data, fc_weights, '
                      'FC_IN, CNN_NUM_OUTPUTS, 0, 7, '
                      f'{"fc_bias" if bias is not None else "NULL"}, '
                      'fc_output, fc_buffer);\n')
        memfile.write('  arm_softmax_q8p7_q15(fc_output, CNN_NUM_OUTPUTS, ml_softmax);\n')
    elif output_width == 32:
        memfile.write('  softmax_q17p14_q15((const q31_t *) ml_data, '
                      'CNN_NUM_OUTPUTS, ml_softmax);\n')
    else:
        memfile.write('  arm_softmax_q7_q15((const q7_t *) ml_data, '
                      'CNN_NUM_OUTPUTS, ml_softmax);\n')

    function_footer(memfile, return_value='void')


def fc_verify(
        memfile,
        sampledata,
        data,
):
    """
    Write the code to verify the fully connected layer to `memfile` against `data`.
    """
    memfile.write('// Expected output of classification layer:\n')
    c_define(sampledata, data, 'FC_EXPECTED', '%d', 16)
    memfile.write('static q15_t fc_expected[CNN_NUM_OUTPUTS] = FC_EXPECTED;\n\n')
    function_header(memfile, prefix='', function='fc_verify')
    function_footer(memfile,
                    return_value='memcmp(fc_output, fc_expected, '
                                 'CNN_NUM_OUTPUTS * sizeof(q15_t)) == 0')


def c_define(
        memfile,
        array,
        define_name,
        fmt,
        columns=8,
):
    """
    Write a #define to `memfile` for array `array` to `define_name`, using format `fmt` and
    creating a line break after `columns` items each.
    `fmt` can have two parts, separated by '%'. The part before the '%' sign is an optional
    prefix and can be empty, the part after the '%' is a formatting directive, e.g. '%08x'.
    """
    prefix, formatting = fmt.split('%')
    memfile.write(f'#define {define_name} {{ \\\n  ')
    for i, e in enumerate(array):
        memfile.write('{prefix}{item:{format}}'.format(prefix=prefix, item=e, format=formatting))
        if i + 1 < len(array):
            memfile.write(', ')
            if (i + 1) % columns == 0:
                memfile.write('\\\n  ')
    memfile.write(' \\\n}\n')


def select_clock(
        memfile,
        source,
        divider,
        comment='',
):
    """
    Switch clock source and divider.
    """
    if comment != '':
        memfile.write(f'  // {comment}\n')
    if source == 'ITO':
        memfile.write('  while ((MXC_GCR->ito_ctrl & MXC_F_GCR_ITO_CTRL_RDY) != '
                      'MXC_F_GCR_ITO_CTRL_RDY) ;\n')
    memfile.write('  MXC_GCR->pclkdiv = (MXC_GCR->pclkdiv & '
                  '~(MXC_F_GCR_PCLKDIV_CNNCLKDIV | MXC_F_GCR_PCLKDIV_CNNCLKSEL))\n'
                  f'                     | MXC_S_GCR_PCLKDIV_CNNCLKDIV_{divider} | '
                  f'MXC_S_GCR_PCLKDIV_CNNCLKSEL_{source};\n')