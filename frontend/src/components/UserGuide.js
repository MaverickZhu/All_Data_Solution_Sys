import React from 'react';
import Joyride, { STATUS } from 'react-joyride';

const UserGuide = ({ run, onTourEnd }) => {
  const steps = [
    {
      target: 'body',
      content: '欢迎来到多模态智能数据分析平台！让我带您快速了解一下主要功能。',
      placement: 'center',
    },
    {
      target: '.create-project-button',
      content: '您可以从这里开始，创建一个新的数据分析项目。',
      placement: 'bottom',
    },
    {
      target: '.projects-list',
      content: '您创建的所有项目都会在这里显示。',
      placement: 'top',
    },
    {
        target: '.project-card-view-button',
        content: '点击这里可以查看项目的详细信息，并开始上传和分析数据。',
        placement: 'bottom',
    },
    {
        target: '.project-card-delete-button',
        content: '如果不再需要某个项目，可以从这里删除它。',
        placement: 'bottom',
    }
  ];

  const handleJoyrideCallback = (data) => {
    const { status } = data;
    if ([STATUS.FINISHED, STATUS.SKIPPED].includes(status)) {
        onTourEnd();
    }
  };

  return (
    <Joyride
      steps={steps}
      run={run}
      continuous
      showProgress
      showSkipButton
      callback={handleJoyrideCallback}
      styles={{
        options: {
          arrowColor: '#fff',
          backgroundColor: '#fff',
          primaryColor: '#007aff',
          textColor: '#333',
          zIndex: 1000,
        },
      }}
    />
  );
};

export default UserGuide; 