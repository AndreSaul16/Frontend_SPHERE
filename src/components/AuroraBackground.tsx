import React from 'react';
import { motion } from 'framer-motion';

export const AuroraBackground: React.FC = () => {
    return (
        <div className="aurora-container">
            {/* Deep Blue Base */}
            <motion.div
                className="aurora-blob w-[600px] h-[600px] bg-blue-900/20 top-[-10%] left-[-10%]"
                animate={{
                    x: [0, 50, 0],
                    y: [0, 30, 0],
                    scale: [1, 1.1, 1],
                }}
                transition={{
                    duration: 20,
                    repeat: Infinity,
                    ease: "easeInOut"
                }}
            />

            {/* Electric Cyan Accent */}
            <motion.div
                className="aurora-blob w-[500px] h-[500px] bg-electric-cyan/10 bottom-[10%] right-[-5%]"
                animate={{
                    x: [0, -40, 0],
                    y: [0, 50, 0],
                    scale: [1, 1.2, 1],
                }}
                transition={{
                    duration: 25,
                    repeat: Infinity,
                    ease: "easeInOut"
                }}
            />

            {/* Luxury Purple Glow */}
            <motion.div
                className="aurora-blob w-[700px] h-[700px] bg-luxury-purple/10 top-[20%] right-[10%]"
                animate={{
                    x: [0, -30, 0],
                    y: [0, -60, 0],
                    rotate: [0, 10, 0],
                }}
                transition={{
                    duration: 30,
                    repeat: Infinity,
                    ease: "easeInOut"
                }}
            />

            {/* Surface Overlay with Noise/Grain if possible but CSS is enough for now */}
            <div className="absolute inset-0 bg-midnight/20 backdrop-blur-[120px]" />
        </div>
    );
};
