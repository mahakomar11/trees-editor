from random import randrange
from googlesheets_utils import SpreadTable
# from excel_utils import ExcelTable


def update_tree(tree, subtree_hierarchy):
    """
    Get subtree with populations that should be in tree, write new populations and delete outdated populations
    tree: pd.DataFrame - old tree (big_tree, Myeloid_cells, etc.)
    subtree_hierarchy: pd.DataFrame - subtree from big hierarchy with columns:
                        BG_population, Parent,	BG_label, To_show, etc.
    :return: new_tree_pos: pd.DataFrame - new tree
    """
    new_tree = subtree_hierarchy.copy()
    for bg_pop, row in subtree_hierarchy.iterrows():
        # Remove not showing pops from new_tree
        if row['To_show'] == 'no':
            new_tree = new_tree.drop(bg_pop)
            continue

        # Find Parent
        parent_to_show = row['Parent']
        # If bg_pop has no Parent, skip
        if parent_to_show == '':
            continue
        # If Parent not in subtree, skip
        if parent_to_show not in subtree_hierarchy.index:
            continue
        # If Parent has To_show = 'no', find Parent of Parent, etc.
        while subtree_hierarchy.at[parent_to_show, 'To_show'] == 'no':
            parent_to_show = subtree_hierarchy.at[parent_to_show, 'Parent']
        # Set Parent to show in new_tree
        new_tree.at[bg_pop, 'Parent'] = parent_to_show

    new_tree = new_tree.reset_index()[['index', 'BG_population', 'Parent', 'BG_label']]
    # For pairs ('BG_population', 'Parent') that has coords, add coords
    new_tree_pos = new_tree.merge(tree.reset_index(), how='left', on=['BG_population', 'Parent'])
    new_tree_pos = new_tree_pos[['index_x', 'BG_population', 'Parent', 'posX', 'posY', 'BG_label_x']] \
        .rename(columns={'index_x': 'index', 'BG_label_x': 'BG_label'}) \
        .fillna('')

    return new_tree_pos


def fill_coords(tree):
    """
    Fill empty posX and posY with random delta from parent's posX and posY.
    tree: pd.DataFrame - a tree that should be plotted (big_tree, Myeloid_cells, etc.)
    :return: tree: pd.DataFrame - a tree with filled positions
    """
    # Find pops without x or y
    empty_pops = tree[(tree['posX'] == '') | (tree['posY'] == '')]

    # Find pops without x or y, that have parent with x and y
    not_empty_parent = empty_pops[(~empty_pops['Parent'].isin(empty_pops.index))
                                  & (empty_pops['Parent'].isin(tree.index))]

    # While there are no populations for which we can calculate position from parent's position
    while len(not_empty_parent) != 0:
        for bg_pop, row in not_empty_parent.iterrows():
            # Add random numbers to Parent's x and y
            tree.at[bg_pop, 'posX'] = tree.at[row['Parent'], 'posX'] + randrange(-30, 30)
            tree.at[bg_pop, 'posY'] = tree.at[row['Parent'], 'posY'] + randrange(-30, 30)
            empty_pops = empty_pops.drop(bg_pop)
        # Find pops without x or y, that have parent with x and y
        not_empty_parent = empty_pops[~empty_pops['Parent'].isin(empty_pops.index)
                                      & (empty_pops['Parent'].isin(tree.index))]

    return tree


if __name__ == '__main__':
    # Load table
    # table = ExcelTable('Cell_hierarchy_try.xlsx')
    table = SpreadTable('Cell_hierarchy.004')

    # tree_names = ['big_tree', 'Myeloid_cells', 'B_cells', 'CD4', 'CD8', 'gd_NK_NKT']
    # tree_names = ['big_tree']
    # tree_names = ['B_cells']
    tree_names = ['Main_cells', 'Myeloid_cells', 'B_cells', 'CD4_differentiation', 'CD4_activation',
                  'CD8_differentiation', 'CD8_activation', 'gd_NK_NKT']
    for tree_name in tree_names:
        print(tree_name)
        # Read existed tree
        tree = table.read_sheet(tree_name)
        tree = tree.set_index('BG_population')
        # Read hierarchy
        hierarchy = table.read_sheet('Show')
        hierarchy = hierarchy.set_index('BG_population')
        # Get subtree of hierarchy to complete tree
        subtree_hierarchy = hierarchy[hierarchy['trees'].str.contains(tree_name)]
        # Update tree and fill coords
        new_tree = update_tree(tree, subtree_hierarchy)
        new_tree_filled = fill_coords(new_tree.set_index('BG_population'))
        # Write updated tree to sheet
        tree_to_write = new_tree_filled.reset_index()
        tree_to_write = tree_to_write[['index', 'BG_population', 'Parent', 'posX', 'posY', 'BG_label']]
        table.write_to_sheet(tree_name, tree_to_write, to_rewrite=True)
    print('ok')
