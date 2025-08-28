import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from pybaseball import statcast_pitcher, playerid_lookup, statcast_batter  # or statcast_batter
import seaborn as sns
import datetime
import numpy as np
from matplotlib.colors import Normalize


class MatchupPlotter:
    def __init__(self, pitcher_first, pitcher_last, batter_first, batter_last, batter_hand, pitcher_hand, pitch_type, batter_color_column='estimated_woba_using_speedangle'):
        self.pitcher_first = pitcher_first
        self.pitcher_last = pitcher_last
        self.batter_first = batter_first
        self.batter_last = batter_last
        self.batter_hand = batter_hand
        self.pitcher_hand = pitcher_hand
        self.batter_color_column = batter_color_column
        self.pitch_type = pitch_type

    def get_data(self):
        pitcher_id = playerid_lookup(self.pitcher_last, self.pitcher_first).key_mlbam.values[0]
        batter_id = playerid_lookup(self.batter_last, self.batter_first).key_mlbam.values[0]

        start_date = '2025-04-01'
        end_date = str(datetime.date.today())

        print(start_date, end_date)

        df_pitcher = statcast_pitcher(start_date, end_date, pitcher_id)
        df_batter = statcast_batter(start_date, end_date, batter_id)

        print("Retrieved data for pitcher:", self.pitcher_first, self.pitcher_last)
        print("Retrieved data for batter:", self.batter_first, self.batter_last)

        return df_pitcher, df_batter
    
    def filter_data(self, df_pitcher, df_batter):
        pitcher_throws = df_pitcher['p_throws'].iloc[0]

        if self.batter_hand == pitcher_throws:
            df_pitcher = df_pitcher[df_pitcher['stand'] == self.batter_hand]
        else:
            df_pitcher = df_pitcher[df_pitcher['stand'].isin([self.batter_hand, 'S'])]
        df_batter = df_batter[df_batter['pitch_type'] == self.pitch_type]
        df_batter = df_batter[df_batter['p_throws'] == self.pitcher_hand]

        print(f"Filtered data for pitcher {self.pitcher_first} {self.pitcher_last} and batter {self.batter_first} {self.batter_last}.")

        return df_pitcher, df_batter
    
    def plot_matchup(self):
        df_pitcher, df_batter = self.get_data()
        df_pitcher, df_batter = self.filter_data(df_pitcher, df_batter)

        # print(df_pitcher.columns[50:])
    
        # df_batter[self.batter_color_column] = df_batter[self.batter_color_column].clip(0.1, 0.6)
        if df_pitcher.empty or df_batter.empty:
            print("No data available for the specified matchup.")
            return
    
        # Filter df_pitcher for the specified pitch type
        df_pitcher_filtered = df_pitcher[df_pitcher['pitch_type'] == self.pitch_type]
        if df_pitcher_filtered.empty:
            print(f"No data available for {self.pitch_type} pitches.")
            return
        
        num_pitches = len(df_batter)
        
    
        # Create a figure with three subplots side by side
        fig, axes = plt.subplots(1, 3, figsize=(18, 8), constrained_layout=True)
        norm = Normalize(vmin=0, vmax=0.7)
    
        # --- Plot 1: xwOBA-Weighted KDE Heatmap for Batter ---
        ax1 = axes[0]
        kde = sns.kdeplot(
            x=df_batter['plate_x'],
            y=df_batter['plate_z'],
            weights=df_batter[self.batter_color_column],
            cmap="coolwarm",
            fill=True,
            bw_adjust=0.5,
            thresh=0.01,
            levels=100,
            clip=[(-2, 2), (0, 5)],
            ax=ax1
        )
        mappable = kde.get_children()[0]  # the QuadMesh
        mappable.set_norm(norm)  # Apply the normalization
        fig.colorbar(mappable, ax=ax1, label='xwOBA-weighted KDE')
    
        # Strike zone box
        ax1.axhline(1.5, color='black', linestyle='--', linewidth=1)
        ax1.axhline(3.5, color='black', linestyle='--', linewidth=1)
        ax1.axvline(-0.83, color='black', linestyle='--', linewidth=1)
        ax1.axvline(0.83, color='black', linestyle='--', linewidth=1)
    
        # Labels and title
        ax1.set_title(f"xwOBA-Weighted KDE Heatmap for {self.batter_first} {self.batter_last} vs {self.pitcher_hand}HP {self.pitch_type} ({num_pitches} pitches)")
        ax1.set_xlabel("Plate X (horizontal)")
        ax1.set_ylabel("Plate Z (vertical)")
        ax1.set_xlim(-2, 2)
        ax1.set_ylim(0, 5)

        pitcher_num_pitches = len(df_pitcher_filtered)
    
        # --- Plot 2: Pitch Density Heatmap ---
        ax2 = axes[1]
        unique_pitch_types = df_pitcher['pitch_type'].unique()
        colors = sns.color_palette("tab10", len(unique_pitch_types))
        pitch_type_colors = {pitch_type: colors[i] for i, pitch_type in enumerate(unique_pitch_types)}
    
        percent_thrown = []
        for pitch_type in unique_pitch_types:
            subset = df_pitcher[df_pitcher['pitch_type'] == pitch_type]
            percent_thrown.append(len(subset) / len(df_pitcher) * 100)  # Calculate percentage of total pitches
            sns.kdeplot(
                x=subset['plate_x'],
                y=subset['plate_z'],
                thresh=0.7,
                levels=100,
                alpha=0.3,
                color=pitch_type_colors[pitch_type],
                ax=ax2
            )
    
        # Strike zone box
        ax2.axhline(1.5, color='black', linestyle='--')  # bottom of strike zone
        ax2.axhline(3.5, color='black', linestyle='--')  # top of strike zone
        ax2.axvline(-0.83, color='black', linestyle='--')  # left edge
        ax2.axvline(0.83, color='black', linestyle='--')  # right edge
    
        # Labels and title
        ax2.set_xlabel("Horizontal Location (plate_x)")
        ax2.set_ylabel("Vertical Location (plate_z)")
        ax2.set_xlim(-1.5, 1.5)
        ax2.set_ylim(0, 5)
        ax2.set_title(f"Pitch Density Heatmap for {self.pitcher_first} {self.pitcher_last} vs {self.batter_hand}HB")
    
        # Custom legend
        handles = [plt.Line2D([0], [0], color=color, lw=4, label=f"{pitch_type} ({percent_thrown[i]:.1f}%)") 
                   for i, (pitch_type, color) in enumerate(pitch_type_colors.items())]
        ax2.legend(handles=handles, title="Pitch Type", loc='upper right')
    
        # --- Plot 3: xwOBA-Weighted KDE Heatmap for Pitcher ---
        ax3 = axes[2]
        kde_pitcher = sns.kdeplot(
            x=df_pitcher_filtered['plate_x'],
            y=df_pitcher_filtered['plate_z'],
            weights=df_pitcher_filtered[self.batter_color_column],
            cmap="coolwarm",
            fill=True,
            bw_adjust=0.5,
            thresh=0.01,
            levels=100,
            clip=[(-2, 2), (0, 5)],
            ax=ax3
        )
        mappable_pitcher = kde_pitcher.get_children()[0]  # the QuadMesh
        mappable_pitcher.set_norm(norm)  # Apply the normalization
        fig.colorbar(mappable_pitcher, ax=ax3, label='xwOBA-weighted KDE')
    
        # Strike zone box
        ax3.axhline(1.5, color='black', linestyle='--', linewidth=1)
        ax3.axhline(3.5, color='black', linestyle='--', linewidth=1)
        ax3.axvline(-0.83, color='black', linestyle='--', linewidth=1)
        ax3.axvline(0.83, color='black', linestyle='--', linewidth=1)
    
        # Labels and title
        ax3.set_title(f"xwOBA-Weighted KDE Heatmap for {self.pitcher_first} {self.pitcher_last} ({self.pitch_type}) vs {self.batter_hand}HB ({pitcher_num_pitches} pitches)")
        ax3.set_xlabel("Plate X (horizontal)")
        ax3.set_ylabel("Plate Z (vertical)")
        ax3.set_xlim(-2, 2)
        ax3.set_ylim(0, 5)
    
        # Show the plots
        plt.show()