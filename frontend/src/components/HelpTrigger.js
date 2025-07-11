import React, { useState } from 'react';
import { QuestionMarkCircleIcon } from '@heroicons/react/24/outline';
import Modal from './Modal';

const HelpTrigger = ({ title, content }) => {
  const [isHelpModalOpen, setHelpModalOpen] = useState(false);

  return (
    <>
      <button
        onClick={() => setHelpModalOpen(true)}
        className="flex items-center justify-center w-8 h-8 rounded-full bg-black bg-opacity-10 hover:bg-opacity-20 text-gray-600 hover:text-gray-900 transition-all duration-200"
        aria-label="获取帮助"
      >
        <QuestionMarkCircleIcon className="h-6 w-6" />
      </button>

      <Modal
        isOpen={isHelpModalOpen}
        onClose={() => setHelpModalOpen(false)}
        title={title || '帮助中心'}
      >
        <div className="prose prose-sm max-w-none text-gray-700">
          {content}
        </div>
      </Modal>
    </>
  );
};

export default HelpTrigger; 