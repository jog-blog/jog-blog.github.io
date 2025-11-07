// 回到顶部按钮实现
class BackToTopButton {
  constructor() {
    this.button = null;
    this.init();
  }

  init() {
    // 检查按钮是否已存在
    if (document.getElementById('back-to-top-button')) {
      return;
    }

    // 创建按钮元素
    const buttonContainer = document.createElement('div');
    buttonContainer.id = 'back-to-top-container';
    buttonContainer.style.position = 'fixed';
    buttonContainer.style.bottom = '32px';
    buttonContainer.style.right = '32px';
    buttonContainer.style.zIndex = '50';
    buttonContainer.style.opacity = '0';
    buttonContainer.style.transform = 'scale(0.5)';
    buttonContainer.style.transition = 'opacity 300ms ease-out, transform 300ms ease-out';

    const button = document.createElement('button');
    button.id = 'back-to-top-button';
    button.ariaLabel = '回到顶部';
    button.style.width = '38px';
    button.style.height = '38px';
    button.style.borderRadius = '50%';
    button.style.backgroundColor = 'var(--primary)';
    button.style.color = 'var(--primary-content)';
    button.style.border = 'none';
    button.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.2)';
    button.style.cursor = 'pointer';
    button.style.display = 'flex';
    button.style.alignItems = 'center';
    button.style.justifyContent = 'center';
    button.style.transition = 'all 300ms ease';
    button.style.outline = 'none';

    // 添加悬停效果
    button.addEventListener('mouseenter', () => {
      button.style.backgroundColor = 'var(--primary-hover)';
      button.style.transform = 'translateY(-2px)';
      button.style.boxShadow = '0 6px 16px rgba(0, 0, 0, 0.25)';
    });

    button.addEventListener('mouseleave', () => {
      button.style.backgroundColor = 'var(--primary)';
      button.style.transform = 'translateY(0)';
      button.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.2)';
    });

    // 添加聚焦效果
    button.addEventListener('focus', () => {
      button.style.boxShadow = '0 0 0 4px rgba(var(--primary), 0.3)';
    });

    button.addEventListener('blur', () => {
      button.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.2)';
    });

    // 添加点击事件
    button.addEventListener('click', () => {
      window.scrollTo({
        top: 0,
        behavior: 'smooth'
      });
    });

    // 创建图标
    const icon = document.createElement('ion-icon');
    icon.setAttribute('name', 'arrow-up-circle-outline');
    icon.setAttribute('size', '24');

    button.appendChild(icon);
    buttonContainer.appendChild(button);
    document.body.appendChild(buttonContainer);

    this.button = buttonContainer;

    // 监听滚动事件
    window.addEventListener('scroll', this.toggleVisibility.bind(this));
    window.addEventListener('resize', this.toggleVisibility.bind(this));

    // 初始检查
    this.toggleVisibility();
  }

  toggleVisibility() {
    if (!this.button) return;

    // 当滚动距离超过300px时显示按钮
    if (window.scrollY > 300) {
      this.button.style.opacity = '1';
      this.button.style.transform = 'scale(1)';
    } else {
      this.button.style.opacity = '0';
      this.button.style.transform = 'scale(0.5)';
    }
  }
}

// 等待DOM加载完成后初始化
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => new BackToTopButton());
} else {
  new BackToTopButton();
}
