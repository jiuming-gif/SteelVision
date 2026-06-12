import matplotlib.pyplot as plt  # 导入Matplotlib库，用于绘制图像

def plot_img_and_mask(img, mask):
    """
    显示输入图像和对应的分割掩码。

    参数:
    img: 输入图像，通常为RGB图像。
    mask: 掩码图像，包含每个像素的类别标签。

    功能:
    该函数将输入图像和不同类别的掩码以子图的形式显示出来。
    """
    classes = mask.max() + 1  # 计算掩码中类别的数量，通过获取掩码中的最大值加1（因为类别从0开始）

    # 创建一个包含多个子图的图形窗口
    # 1行（行数为1），classes+1列（列数为类别数加1，包含原图）
    fig, ax = plt.subplots(1, classes + 1)

    # 显示输入图像
    ax[0].set_title('Input image')  # 设置第一个子图的标题为 "Input image"
    ax[0].imshow(img)  # 在第一个子图中显示输入图像

    # 显示每个类别的掩码
    for i in range(classes):  # 遍历所有类别
        ax[i + 1].set_title(f'Mask (class {i + 1})')  # 为每个类别掩码设置标题，标注类别编号
        ax[i + 1].imshow(mask == i)  # 在子图中显示当前类别的掩码，mask == i 用于显示属于当前类别的像素

    # 隐藏所有子图的坐标轴刻度
    plt.xticks([]), plt.yticks([])  # 隐藏x轴和y轴的刻度
    plt.show()  # 显示图像
