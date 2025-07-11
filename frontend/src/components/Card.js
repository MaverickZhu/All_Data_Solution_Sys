import React from 'react';

const Card = ({ 
  children, 
  title, 
  subtitle,
  actions,
  className = '',
  hover = false,
  ...props 
}) => {
  const baseClasses = 'bg-white rounded-lg shadow-md border border-gray-200 overflow-hidden';
  const hoverClasses = hover ? 'hover:shadow-lg transition-shadow duration-200' : '';
  
  const cardClasses = [
    baseClasses,
    hoverClasses,
    className
  ].join(' ');
  
  return (
    <div className={cardClasses} {...props}>
      {(title || subtitle || actions) && (
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-start justify-between">
            <div>
              {title && (
                <h3 className="text-lg font-semibold text-gray-900 mb-1">
                  {title}
                </h3>
              )}
              {subtitle && (
                <p className="text-sm text-gray-600">
                  {subtitle}
                </p>
              )}
            </div>
            {actions && (
              <div className="flex items-center gap-2">
                {actions}
              </div>
            )}
          </div>
        </div>
      )}
      <div className="px-6 py-4">
        {children}
      </div>
    </div>
  );
};

export default Card; 